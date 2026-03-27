# Architecture

## Class Hierarchy

```
Tester (ABC)                          tester/Tester.py
  ├── RunExecutorMixin                tester/RunExecutor.py
  └── StateManagerMixin              tester/StateManager.py
        │
        ├── TestDB                   tester/TestDB.py
        │     └── DatabaseInterface  tester/database/base.py
        │           ├── SQLiteDatabase      tester/database/sqlite_db.py
        │           └── PostgreSQLDatabase  tester/database/postgres_db.py
        │
        ├── TesterIf                 tester/TesterIf.py   (Flask + SocketIO server)
        │
        ├── Dut                      tester/Dut.py
        │     ├── TestProgram        tester/TestProgram.py
        │     └── TestSuite          tester/TestSuite.py
        │           └── TestCase (ABC)     tester/TestCase.py
        │                 └── TestResult (ABC)  tester/TestResult.py
        │                       ├── NumericTestResult
        │                       ├── StringTestResult
        │                       ├── BoolTestResult
        │                       ├── PassFailTestResult
        │                       └── Numeric2dTestResult
        │
        ├── TestRun                  tester/TestRun.py
        ├── TestReport               tester/TestReport.py
        ├── TestDialog               tester/TestUtil.py  (singleton)
        ├── TestAttachment           tester/TestUtil.py  (singleton)
        └── TestLogger               tester/TestLogger.py (singleton)
```

---

## Tester Decomposition

`Tester` is split into three classes via Python mixins to keep the code manageable:

### `RunExecutorMixin` (`RunExecutor.py`)

All test execution logic:
- `run()` / `_run()` — starts the run thread
- `_execute_testsuite()` — iterates setup → testcases → cleanup for one suite
- `_create_run()` — builds the `TestRun` object and merges attr chains
- `_store_original_skip_states()` / `_track_program_modifications()` — tracks operator skip changes
- `wait_for_test_end()` — blocks until the run thread finishes
- `_ctype_async_raise()` — injects `AbortRunException` into the run thread using CPython internals

### `StateManagerMixin` (`StateManager.py`)

UI state construction and Socket.IO emission:
- `_generate_state()` — full state rebuild (called on connect)
- `_update_tester()` / `_update_dut()` / `_update_program()` / `_update_run()` — partial state pushes
- `_timer_update()` — fires every 500 ms during a run to push elapsed time

### `Tester` (`Tester.py`)

Wire-up only:
- Reads config files, instantiates DB, duts, interface
- Registers all Socket.IO event handlers by assigning to `TesterIf` handler slots
- Implements `_init()` abstract method contract
- Provides `select_dut()` / `select_program()` (including user skip-state preservation across program changes)

---

## Server (`TesterIf`)

`TesterIf` wraps Flask and Flask-SocketIO. It runs in threading mode on port 5050.

**Static file serving:** The Next.js build outputs to `tester/frontend/`. Flask serves this directory:
- `/` → `frontend/index.html`
- `/results` → `frontend/results.html`
- `/test-query` → `frontend/test-query.html`
- `/_next/...` → static assets

**Socket.IO events** (server → client):

| Event | Payload | When emitted |
|---|---|---|
| `state` | Full state dict | On client connect, and on reload |
| `tester` | Tester status slice | Every 500 ms during run, on status change |
| `active_dut` | DUT info | On DUT change |
| `active_program` | Program + test cases | On program change |
| `run` | Full list of test results | At run start and on stop |
| `run_item` | Single updated result `{idx, item}` | After each test completes |
| `log` | Log line string | Every `TestLogger` emit |
| `log_clear` | _(empty)_ | At the start of each run |
| `test_execute_state` | `{test_id, execute}` | When skip state changes |
| `dialog` | Dialog state (via tester) | Via `tester` event payload |

**Socket.IO events** (client → server):

| Event | Payload | Effect |
|---|---|---|
| `get_state` | — | Server emits `state` |
| `start_run` | — | Starts the run thread |
| `stop_run` | — | Injects abort into run thread |
| `set_dut` | `{dut: name}` | `select_dut()` |
| `set_program` | `{program: name}` | `select_program()` |
| `reload` | — | Re-reads `duts.json` |
| `attr` | `{key: value, ...}` | Updates `run_attr` |
| `test_execute_state` | `{test_id, execute, type, suite, name}` | Toggles skip state |
| `dialog_response` | `{rsp}`, `data` | Releases the dialog semaphore |

**HTTP endpoints:**

| Path | Description |
|---|---|
| `GET /get_report` | Downloads the HTML report for the latest run |
| `GET /get_runs` | JSON list of all runs (for the Runs page) |
| `GET /generate_report/<id>` | Downloads the HTML report for run `<id>` |
| `GET /show_report/<id>` | Shows the HTML report for run `<id>` in the browser |
| `GET /get_available_tests` | Unique test names from the database |
| `GET /get_available_programs` | Unique program names from the database |
| `GET /get_available_duts` | Unique DUT names from the database |
| `GET /query_test_results` | Query test results with filters (used by Tests page) |
| `GET /dut_image` | DUT image for the active DUT |
| `POST /req/` | Programmatic control (run, stop) |

---

## Database

`TestDB` is a thin façade that delegates to either `SQLiteDatabase` or `PostgreSQLDatabase` depending on whether `db_config` starts with `postgresql://`.

Both implement `DatabaseInterface`, which defines:
- `create_run(run)` → `int` — inserts run metadata, returns run ID
- `update_run_end(run)` — writes end time, result, and attachment
- `append_result(result, run_id)` — inserts one test result row
- `get_run(id)` → `TestRun` — reconstructs a full run from the database
- `get_runs()` → JSON string — summary list for the Runs page
- `get_available_tests/programs/duts()` → `list[str]`
- `query_test_results(params)` → `list[dict]` — filtered query for the Tests page

The shared `_build_query_filters()` method on `DatabaseInterface` constructs the WHERE clause from a params dict (handles both `?` for SQLite and `%s` for PostgreSQL).

---

## Frontend

The frontend is a **Next.js 13 App Router** static export (`output: 'export'`). It is built with `npm run build` in `tester-frontend/` and the output goes directly to `tester/frontend/` (set by `distDir` in `next.config.js`). The Flask server then serves it as static files.

All pages and components are client components (`'use client'`). There are no server components with data fetching — all data flows through Socket.IO or REST.

**State flow:**
1. Browser connects via Socket.IO.
2. Backend sends the full `state` object.
3. `ConnectionContext` stores it and exposes it via `useConnection()`.
4. Subsequent targeted events (`tester`, `run`, `active_program`, etc.) update specific slices.

**Key React contexts:**
- `SocketContext` — the `socket.io-client` instance; allows child components to emit events
- `ConnectionContext` — online/offline/connecting status; consumed by all pages to show the disconnection overlay

---

## Singletons

Three services are implemented as Python singletons (via a `Singleton` metaclass):

| Singleton | Purpose |
|---|---|
| `TestLogger` | Shared logger instance; initialised once by `Tester`, used everywhere |
| `TestDialog` | Shared dialog state; `Tester` holds a reference; test cases use `self.dialog` |
| `TestAttachment` | Shared attachment accumulator; bound to the active `TestRun` at run start |

The singleton pattern ensures that test case code can access these services without needing a reference to the `Tester` instance itself.

---

## Attribute Merge Chain

Attributes (`attr`) flow down the configuration hierarchy. At each level the more specific value wins (Python dict `|` merge, rightmost wins):

```
TestCase.config.attr defaults
  | TestSuite.attr (from duts.json suite level)
  | TestProgram.attr (from duts.json program level)
  | per-program ts_attr (from the testsuites list entry)
  | run_attr (DUT.attr merged with active_program.attr + operator UI edits)
```

The final merged `config.attr` is what `_execute(config, assets)` receives.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **Hardware-in-the-Loop (HiL) test framework** consisting of:
- **`tester/`** — Python package (the framework itself)
- **`tester-frontend/`** — Next.js 13 frontend source
- **`tester/frontend/`** — Built frontend output (served by Flask; never edit directly)
- **`example_tester/`** — Reference implementation showing how to use the framework
- **`tests/`** — pytest suite for the backend

## Commands

### Backend

```bash
# Install backend in editable mode (run from repo root)
pip install -e .

# Run all tests
pytest

# Run a single test file
pytest tests/unit/test_test_run.py

# Run a single test by name
pytest tests/integration/test_tester.py::test_run_pass

# Run the example tester (starts Flask UI on http://localhost:5050)
cd example_tester && python example_tester.py
```

### Frontend

All commands run from `tester-frontend/`:

```bash
npm install          # install dependencies
npm run build        # production build → outputs to tester/frontend/
npm run dev          # dev server (hot reload, for frontend-only work)
npm run lint         # ESLint
```

**After any frontend source change**, you must `npm run build` for the Flask server to serve the new version. The Next.js config (`next.config.js`) sets `distDir: '../tester/frontend'` and `output: 'export'`, so the build writes directly into the Python package's static directory.

## Architecture

### Python Backend (`tester/`)

The framework is used by subclassing `Tester` and implementing `_init()`:

```python
class MyTester(Tester):
    def _init(self, station_config: StationConfig) -> dict:
        # Open hardware connections here; return an assets dict
        return {"instrument": MyInstrument(station_config.serial_port)}
```

**Key class hierarchy:**

```
Tester (ABC)
  ├── RunExecutorMixin    — test execution logic (run threading, skip tracking)
  └── StateManagerMixin  — UI state building and Socket.IO emission

Dut               — loaded from duts.json; owns TestPrograms and TestSuites
TestProgram       — ordered list of TestSuite references with attr merging
TestSuite         — setup + list[TestCase] + cleanup
TestCase (ABC)    — implement _execute(); return value is auto-evaluated
TestResult (ABC)  — wraps value + tolerance; implements _evaluate()
TestRun           — in-progress run state; written to DB on completion
                    - `serial_number` — unit serial number entered by the operator before the run (stored in DB, shown in report and run list)
                    - `config_hash` — SHA-256 of `duts.json` at run time (stored in DB, shown in report; use to verify which test limits were active)
```

**TestCase types** (in `tester/TestResults/`): each pairs a `TestCase` subclass with a `TestResult` subclass:
- `NumericTestResult` / `NumericTestCase` — min/max tolerance
- `StringTestResult` / `StringTestCase` — exact string match
- `BoolTestResult` / `BoolTestCase` — boolean expected value
- `PassFailTestResult` / `PassFailTestCase` — pass/fail with no measurement
- `Numeric2dTestResult` / `Numeric2dTestCase` — X/Y array with per-point tolerance (renders a plot in the UI)

**Configuration files** (all JSON5-compatible via `pyjson5`):
- `duts.json` — defines DUTs, test suites, programs, and their relationships
- `setup.json` / `station.json` — station-specific hardware config, validated against a `StationConfig` Pydantic model
- `TesterConfig` dataclass — wires everything together; `db_config` is either a file path (SQLite) or a PostgreSQL connection string

**Attribute (`attr`) merge chain** (later wins):
```
TestCase defaults → TestSuite.attr → TestProgram.attr → per-program ts_attr override → run_attr (user edits)
```
`config.attr` is available inside `_execute()` on every test case.

**Database abstraction** (`tester/database/`): `DatabaseFactory` returns either `SQLiteDatabase` or `PostgreSQLDatabase` based on whether `db_config` starts with `postgresql://`. Both implement `DatabaseInterface`.

**Server** (`TesterIf`): Flask + Flask-SocketIO (threading mode) on port 5050. Socket.IO events carry live state (`tester`, `run`, `state`, `log`, etc.). The `TesterRequest` enum defines all event names.

### Frontend (`tester-frontend/`)

Next.js 13 App Router with `output: 'export'` (static export). All pages are client components (`'use client'`).

**Three pages:**
- `/` (`app/page.jsx`) — live dashboard: DUT/program selector, run controls, test result table, log modal
- `/results` (`app/results/page.jsx`) — historical run browser
- `/test-query` (`app/test-query/page.jsx`) — cross-run test result query and histogram

**Key components:**
- `socket.jsx` — Socket.IO client singleton + `SocketContext`
- `contexts/ConnectionContext.jsx` — `ConnectionProvider` wraps the app; exposes `useConnection()` for live tester state
- `components/Providers.jsx` — MUI ThemeProvider
- `components/NavBar.jsx` — navigation + live tester name
- `components/TestResultRow.jsx` — single row in the run table, includes execute checkbox and `ResultPlot`
- `components/TestDialog.jsx` — modal dialog driven by backend (JSONForms for dynamic inputs)

**Important:** Every component file that uses React hooks or browser APIs must have `'use client'` as its first line. The static export does not support server components with client-side interactivity.

**Socket.IO state flow**: On connect, the backend emits the full `state` object. Subsequent updates emit targeted slices (`tester`, `run`, `active_program`, etc.) which are merged into `ConnectionContext` state.

## Test Structure

Tests live in `tests/`. The `conftest.py` provides:
- `headless_tester` fixture — pre-built `MinimalTester` (SQLite in `tmp_path`, `ui=False`)
- `make_tester(duts_data)` factory fixture — for custom DUT configurations
- Several `DUTS_*` constants for common test scenarios

`tests/fixtures/fast_tests.py` contains lightweight `TestCase` implementations (instant pass/fail/slow) used by integration tests. The `tests/` directory is added to `sys.path` by `conftest.py` so `duts.json` module references like `"module": "fixtures.fast_tests"` resolve correctly.

## Traceability

Two fields are automatically recorded with every test run for ISO 9001 compliance:

- **Serial number** (`runs.serial_number`): the unit-under-test serial number. Set via the "Unit Serial Number" input in the dashboard UI, or programmatically via `tester.serial_number = 'SN-xxx'` before calling `run()`. Shown in the HTML report and the runs list.
- **Config hash** (`runs.config_hash`): SHA-256 of `duts.json` at the moment the run starts. Computed automatically; shown (truncated) in the HTML report. Use it to verify that two runs used identical test limits and sequences.

## Adding a New Test Case Type

1. Create a file in `tester/TestResults/` with paired `XxxTestCase(TestCase)` and `XxxTestResult(TestResult)` classes
2. Implement `_evaluate()`, `_min_str()`, `_max_str()`, `_value_str()`, `value_from_str()`, and `result_type` on the result class
3. Export from `tester/TestResults/__init__.py`
4. Add deserialization in `TestResultFactory`

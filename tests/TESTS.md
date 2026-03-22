# Backend Test Suite

This document describes the structure, purpose, and coverage of the backend
test suite located in `tests/`.  Frontend tests are planned as a separate
phase and are not included here.

---

## Running the tests

```bash
# From the repo root (activate the tester venv first)
pytest tests/ -v

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v

# Run with coverage report
pytest tests/ --cov=tester --cov-report=term-missing
```

> **Note:** The integration tests import test-case classes from
> `tests/fixtures/fast_tests.py` using the module path `fixtures.fast_tests`.
> `conftest.py` inserts `tests/` onto `sys.path` at session start so this
> works automatically when running pytest from any directory.

---

## Directory layout

```
tests/
├── conftest.py                      # shared fixtures and MinimalTester
├── TESTS.md                         # this file
├── fixtures/
│   ├── __init__.py
│   └── fast_tests.py                # fast concrete TestCase subclasses
├── unit/
│   ├── test_result_types.py         # all 5 TestResult subtypes
│   ├── test_test_config.py          # TestConfig.from_dict
│   ├── test_station_config.py       # StationConfig pydantic base
│   ├── test_test_run.py             # TestRun lifecycle & aggregation
│   └── test_test_result_factory.py  # TestResultFactory singleton & from_dict
└── integration/
    ├── test_test_case.py            # TestCase.execute / skip / exception handling
    ├── test_test_suite.py           # TestSuite.from_dict & attr inheritance
    ├── test_database.py             # SQLiteDatabase CRUD, role filter, migration
    └── test_tester.py               # full Tester run lifecycle
```

---

## Fixtures (`conftest.py`)

| Fixture | Scope | Description |
|---|---|---|
| `init_logger` | session | Initialises the `TestLogger` singleton once with `dirname=None` (no file output). Required by all tests that invoke `TestCase.execute()`. |
| `make_tester(duts_data)` | function | Factory: writes `duts.json` + `station.json` to `tmp_path`, instantiates a headless `MinimalTester`, yields the factory function, and calls `wait_for_test_end()` on teardown. |
| `headless_tester` | function | Convenience wrapper: `make_tester(DUTS_STANDARD)`. |

**Pre-defined duts data sets** in `conftest.py`:

| Name | Description |
|---|---|
| `DUTS_STANDARD` | DUT with passing setup/cleanup; one suite containing `FastPassTest` and `FastFailTest`. |
| `DUTS_DUT_SETUP_FAIL` | DUT-level setup uses `FastSetupFailTest` → should cascade-skip all suites. |
| `DUTS_SLOW` | One suite containing `SlowTest` (30-second sleep) followed by `FastPassTest`. Used only for abort tests. |
| `DUTS_ATTR_READ` | DUT attr `read_key=from_dut`, program attr `read_key=from_program`; suite contains `AttrReadTest`. |

---

## Unit tests

### `test_result_types.py` — `TestResult` evaluation logic

Tests each of the five result subtypes in isolation by constructing result
objects directly and checking the `result` field.

| Area | Tests |
|---|---|
| **NumericTestResult** | pass within range, pass at both boundaries, fail below min, fail above max, error on non-numeric value, `result_type` constant, `value_from_str` |
| **StringTestResult** | pass on exact match, fail on mismatch, fail on case difference, error on non-string value, `result_type`, `value_from_str` |
| **BoolTestResult** | pass true/true, pass false/false, fail true/false, fail false/true, error on string `"True"`, `result_type`, `value_from_str` both directions |
| **PassFailTestResult** | pass, fail, error on non-TestEval value, `result_type`, `value_from_str` |
| **Numeric2dTestResult** | pass (all points in range), fail (one point out), raises on missing `y` key, raises on non-dict value, `result_type`, `plot_data` populated after evaluation |
| **Common behaviour** | `infoonly=True` overrides FAIL→INFOONLY, `skip=True` overrides PASS→SKIPPED, `role` defaults to `"testcase"`, `to_dict()` contains all required keys |

### `test_test_config.py` — `TestConfig.from_dict`

Verifies that every field has the correct default value when the input dict
is empty, and that all fields are populated correctly when the full dict is
supplied.  Also verifies that unknown keys are silently ignored.

### `test_station_config.py` — `StationConfig` Pydantic base

| Area | Tests |
|---|---|
| Base class | validates an empty dict, ignores extra fields |
| Subclass defaults | all default values present when dict is empty |
| Subclass overrides | individual fields overridable; unspecified fields keep defaults |
| Extra fields | unknown JSON keys silently ignored (`extra='ignore'`) |
| Type validation | wrong type raises `pydantic.ValidationError` for `float` and `int` fields |

### `test_test_run.py` — `TestRun`

| Area | Tests |
|---|---|
| Construction | initial field values, `program_attr` stored, `program_modified` defaults to `False` |
| `append_result` | result added to `test_results` list |
| Lifecycle | `start()` sets `start_date`, `end()` sets `end_date` and triggers `evaluate()` |
| Aggregation | all PASS→PASS, any FAIL→FAIL, FAIL beats ERROR, ERROR only→ERROR, any ABORTED→ABORTED, all SKIPPED→UNKNOWN, empty run→UNKNOWN |
| `from_dict` | reconstructs `dut`, `program`, `program_attr`, `result`, `log` from serialised dict |

### `test_test_result_factory.py` — `TestResultFactory`

| Area | Tests |
|---|---|
| Singleton | two calls return the same instance |
| Built-in registrations | `numeric`, `string`, `bool`, `none` (PassFail), `numeric2d` all present |
| `from_dict` | reconstructs correct subtype for each built-in type; preserves `value`, `name`, `suite`, `comment`; stored `result` overrides re-evaluation |
| `add()` | registers a custom subtype; verifies it appears in `tr_dict` |

---

## Integration tests

### `test_test_case.py` — `TestCase` execution

Constructs concrete `TestCase` subclasses directly (no file loading, no
Tester).

| Test | What it verifies |
|---|---|
| `test_execute_pass/fail` | `_execute` return value maps to correct `result` |
| `test_execute_exception_gives_error` | uncaught exception → `ERROR`, message in `comment` |
| `test_execute_abort_exception_gives_aborted` | `AbortRunException` → `ABORTED` |
| `test_skip_gives_skipped` | `tc.skip()` → `SKIPPED`, `date` set |
| `test_skip_does_not_call_execute` | error-raising case stays `SKIPPED` after `skip()` |
| `test_set_comment_*` | `set_comment()` persists to `result.comment`; works from inside `_execute` |
| `test_is_executing_*` | class flag is `True` during `_execute`, `False` after |
| `test_infoonly_overrides_out_of_range_value` | `infoonly=True` config → `INFOONLY` even when value would FAIL |
| `test_execute_sets_result_date` | `result.date` is set after execute |

### `test_test_suite.py` — `TestSuite.from_dict`

Uses `fixtures.fast_tests` module; no Tester, no database.

| Test | What it verifies |
|---|---|
| Structure | name, presence/absence of setup & cleanup, testcase count |
| Module loading | correct classes instantiated; setup executes PASS; TCs execute PASS/FAIL |
| Attr inheritance | suite `attr` flows to setup, cleanup, and testcases |
| Attr merge | testcase attr merged with suite attr; testcase key wins for same key |
| `debug_reload=False` | does not raise |

> **Cascade behaviour** (setup FAIL → testcases SKIPPED) is tested in
> `test_tester.py` because it is implemented by `RunExecutorMixin._execute_testsuite`.

### `test_database.py` — `SQLiteDatabase`

Uses a real SQLite file in `tmp_path`; no Tester.

| Area | Tests |
|---|---|
| CRUD | `create_run` returns positive integer ID; `get_run` reconstructs DUT & program; `get_run` raises `ValueError` for unknown ID |
| `append_result` | result stored and retrievable via `get_run` |
| `update_run_end` | `program_modified` flag persisted correctly (True and False) |
| `get_runs` | returns JSON string; multiple runs listed |
| **Role filter** | `setup` and `cleanup` roles excluded from `get_available_tests()`; `testcase` role included; results deduplicated across runs; empty DB returns `[]` |
| Programs / DUTs | `get_available_programs` and `get_available_duts` deduplicate correctly |
| **`query_test_results`** | filter by `dut`, `program`, `test_name`, `test_names` (comma-separated); setup/cleanup roles excluded from all queries; result dict includes `DUT` and `Program` keys |
| **Migration** | existing DB without `role` column gets it added; existing DB without `program_modified` gets it added; both migrate without raising |

### `test_tester.py` — Full Tester lifecycle

Uses the `make_tester` factory; runs against real SQLite via `TestDB`.

| Area | Tests |
|---|---|
| **DUT / program selection** | `active_dut` and `active_program` set correctly on construction; `select_program` by name; second `run()` call raises `RuntimeError` |
| **Full run** | run completes (`running=False`, `end_date` set); results written to DB; individual pass/fail tests have correct result; overall run result is FAIL when any test fails; status resets to "Idle" |
| **Statistics** | `test_stats['total']` equals result count; `done` equals `total`; PASS and FAIL counters match actual results |
| **DUT setup failure** | DUT setup FAIL → all suite testcases SKIPPED; overall run result is not PASS |
| **Suite setup failure** | Suite setup FAIL → testcases in that suite SKIPPED; cleanup still executes |
| **Attr hierarchy** | program attr wins over DUT attr for same key (verified via `AttrReadTest`); user attr from `_attr_handler` wins over program attr |
| **Skip-by-user** | `_test_execute_state_handler(execute=False)` → result is SKIPPED with "Skipped by user" comment; skip state preserved across `select_program` re-call |
| **`program_modified` flag** | set to `True` when user skips a test; remains `False` with no user changes |
| **Abort** | mid-run `_stop_run_handler()` → interrupted test is ABORTED; subsequent tests are SKIPPED; `abort_run` flag reset to `False` after run ends |
| **Reload** | `_reload_handler()` preserves active DUT and program selection |

---

## Coverage summary

| Framework component | Test file(s) |
|---|---|
| `TestResult` (base + all 5 subtypes) | `unit/test_result_types.py` |
| `TestConfig` | `unit/test_test_config.py` |
| `StationConfig` | `unit/test_station_config.py` |
| `TestRun` | `unit/test_test_run.py` |
| `TestResultFactory` | `unit/test_test_result_factory.py` |
| `TestCase` | `integration/test_test_case.py` |
| `TestSuite` | `integration/test_test_suite.py` |
| `SQLiteDatabase` | `integration/test_database.py` |
| `TestDB` (wrapper) | `integration/test_tester.py` (via Tester.db) |
| `Tester` / `RunExecutorMixin` | `integration/test_tester.py` |
| `StateManagerMixin` | `integration/test_tester.py` (state updated after each run) |
| `Dut.from_dict` | `integration/test_tester.py` (Tester.populate_duts) |
| `TestProgram.from_dict` | `integration/test_tester.py` (Dut.from_dict) |
| `TesterConfig` | `integration/test_tester.py` (MinimalTester construction) |
| `TestLogger` (singleton) | All tests that invoke `TestCase.execute()` |
| `debug_reload` flag | `integration/test_test_suite.py` |

### Intentionally not covered (Phase 2)

| Component | Reason |
|---|---|
| `TesterIf` (WebSocket) | Requires a real socket client; deferred to frontend test phase |
| `TestReport` (HTML generation) | UI concern; deferred to frontend test phase |
| `PostgreSQLDatabase` | Requires a running PostgreSQL instance; patterns are identical to SQLite |
| `TestAttachment` | File I/O wrapper; low risk, simple utility |

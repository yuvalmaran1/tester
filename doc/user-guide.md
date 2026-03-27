# User Guide

This guide walks through everything needed to build a complete tester using the framework.

## Table of Contents

1. [Overview of the hierarchy](#1-overview-of-the-hierarchy)
2. [Subclassing Tester](#2-subclassing-tester)
3. [Station configuration](#3-station-configuration)
4. [Writing test cases](#4-writing-test-cases)
5. [duts.json reference](#5-dutsjson-reference)
6. [Test programs and test suites](#6-test-programs-and-test-suites)
7. [Attributes (attr)](#7-attributes-attr)
8. [Skip / infoonly](#8-skip--infoonly)
9. [Programmatic control (no UI)](#9-programmatic-control-no-ui)

---

## 1. Overview of the Hierarchy

```
Tester
└── Dut  (one or more physical device types)
    ├── setup / cleanup  (DUT-level; runs once before/after all suites)
    ├── TestSuite  (a logical group of related tests; defined on the DUT)
    │   ├── setup  (runs before tests in this suite; if it fails, tests are skipped)
    │   ├── TestCase  (one measurable quantity)
    │   └── cleanup  (runs after tests in this suite regardless of results)
    └── TestProgram  (a named sequence of TestSuites; defined on the DUT)
        └── references to TestSuites (ordered, may repeat, may override attr)
```

A **DUT** represents a type of hardware (e.g. "Board Rev A"). A DUT can have multiple **programs** (e.g. "Quick Sanity", "Full Production"). Each program is an ordered list of **test suites** selected from the DUT's suite pool. When the operator presses Run, the selected program executes from top to bottom.

---

## 2. Subclassing Tester

Every tester application starts by subclassing `Tester` and implementing `_init()`:

```python
from tester import Tester, TesterConfig
from tester.StationConfig import StationConfig

class MyTester(Tester):
    def __init__(self):
        cfg = TesterConfig(
            name="My Production Tester",
            description="Tests the 3V3 power rails",
            version="2.1.0",
            db_config="./results.db",          # SQLite path (or PostgreSQL URL)
            setup_file="./station.json",        # fallback config file
            duts_file="./duts.json",
            log_dir="./logs",                   # None to disable file logging
            ui=True,                            # False to skip Flask startup
            station_config_file="./station.json",
            station_config_class=MyStationConfig,
            debug_reload=False,                 # True to reload test modules on each run
        )
        super().__init__(cfg)

    def _init(self, station_config: MyStationConfig) -> dict:
        """
        Called once at startup. Open hardware connections here.
        Return a dict of objects that your test cases will need — the 'assets'.
        """
        instrument = MyInstrument(station_config.serial_port)
        power_supply = MyPowerSupply(station_config.ip_address)
        return {
            "instrument": instrument,
            "psu": power_supply,
        }

if __name__ == "__main__":
    MyTester()
```

`_init()` receives the validated `StationConfig` subclass and must return a plain `dict`. That dict is passed to every test case as `assets`. Assets are shared across all test cases and all runs without re-initialisation.

### TesterConfig fields

| Field | Required | Description |
|---|---|---|
| `name` | yes | Display name shown in the UI and reports |
| `version` | yes | Your application version string |
| `db_config` | yes | SQLite file path or `postgresql://...` URL |
| `duts_file` | yes | Path to `duts.json` |
| `setup_file` | yes | Path to a JSON file used as fallback station config |
| `description` | no | Shown in the UI subtitle |
| `log_dir` | no | Directory for log files; `None` disables file logging |
| `ui` | no | `True` (default) starts the Flask server; `False` skips it |
| `station_config_file` | no | Path to station JSON (preferred over `setup_file`) |
| `station_config_class` | no | Pydantic `StationConfig` subclass to validate the file |
| `debug_reload` | no | `True` reloads test modules each run — useful during development |

---

## 3. Station Configuration

`StationConfig` is a [Pydantic](https://docs.pydantic.dev/) `BaseModel` that validates the per-station JSON file. Subclass it to declare the hardware parameters for your bench:

```python
from tester.StationConfig import StationConfig

class MyStationConfig(StationConfig):
    serial_port: str = "COM1"
    ip_address: str = "192.168.1.1"
    calibration_offset: float = 0.0
    use_external_clock: bool = False
```

Fields not present in the JSON file take their default values. Extra keys in the JSON file are silently ignored.

The validated config object is passed to `_init()` and its fields are accessed by name:

```python
def _init(self, station_config: MyStationConfig) -> dict:
    port = station_config.serial_port      # type: str
    offset = station_config.calibration_offset  # type: float
    ...
```

---

## 4. Writing Test Cases

Each test case is a class that inherits from one of the five result-type base classes (see [Test Result Types](test-result-types.md)). You implement one method: `_execute()`.

```python
from tester.TestResults.NumericTestResult import NumericTestCase
from tester.TestConfig import TestConfig

class SupplyVoltageTest(NumericTestCase):
    def _execute(self, config: TestConfig, assets: dict) -> float:
        # config.tolerance   → {"min": 3.2, "max": 3.4}
        # config.attr        → merged attr dict (program + suite + test level)
        # config.name        → "3.3V Rail"
        # config.unit        → "V"
        # assets             → whatever _init() returned
        return assets["psu"].measure_3v3()
```

Rules:
- Return the measured value. The framework calls `result.evaluate()` automatically.
- Raise any exception to mark the test as **ERROR** (the exception message is stored as the comment).
- Call `self.set_comment("note")` to attach a free-text comment to the result.
- Call `self.assets["attachment"].attach_file(path)` to attach a file (see [Utilities](utilities.md)).
- Raise `AbortRunException` (imported from `tester.TestUtil`) to stop the entire run gracefully.

### Setup and cleanup test cases

Setup and cleanup use `PassFailTestCase`. If a **suite setup** returns anything other than `PASS`, all test cases in that suite are automatically skipped (but cleanup still runs):

```python
from tester.TestResults.PassFailTestResult import PassFailTestCase
from tester.TestResult import TestResult

class PowerOnSetup(PassFailTestCase):
    def _execute(self, config, assets) -> TestResult.TestEval:
        if not assets["psu"].power_on():
            return TestResult.TestEval.FAIL
        return TestResult.TestEval.PASS

class PowerOffCleanup(PassFailTestCase):
    def _execute(self, config, assets) -> TestResult.TestEval:
        assets["psu"].power_off()
        return TestResult.TestEval.PASS
```

---

## 5. duts.json Reference

`duts.json` is a JSON5 file (comments allowed, trailing commas OK) with a single top-level key `"duts"` containing an array of DUT objects.

### Full structure

```jsonc
{
  "duts": [
    {
      // --- Identity ---
      "name":        "Board Rev A",          // shown in UI and reports
      "description": "Main controller PCB",
      "product_id":  "PCB-001-A",
      "image":       "./assets/board.png",   // shown in reports (relative to duts.json)

      // --- DUT-level attributes (inherited by all suites/tests) ---
      "attr": { "hw_rev": "A" },

      // --- DUT-level setup / cleanup (optional) ---
      // If setup fails, ALL test suites are skipped.
      "module":  "tests.generic",
      "setup":   "PowerOnSetup",
      "cleanup": "PowerOffCleanup",

      // --- Test suite pool (referenced by programs) ---
      "testsuites": [
        {
          "name":   "Power Rails",
          "module": "tests.power_tests",
          "setup":   "RailsSetup",    // optional
          "cleanup": "RailsCleanup",  // optional
          "attr": { "supply_voltage": 3.3 },
          "testcases": [
            {
              "name":      "3.3V Rail",
              "test":      "VoltageTest",
              "module":    "tests.power_tests",  // optional: overrides suite module
              "tolerance": { "min": 3.2, "max": 3.4 },
              "unit":      "V",
              "infoonly":  false,   // true → result is always INFOONLY, never PASS/FAIL
              "skip":      false,   // true → skipped by default
              "attr":      {}       // test-level attr override
            }
          ]
        }
      ],

      // --- Programs ---
      "programs": [
        {
          "name":        "Production",
          "description": "Full production test",
          // JSON Schema for editable attributes shown in the UI
          "attr_schema": {
            "type": "object",
            "properties": {
              "fw_version": { "type": "string", "description": "FW version under test" }
            }
          },
          "attr": { "fw_version": "1.0.0" },
          // Ordered list of suites to run (strings or objects)
          "testsuites": [
            "Power Rails",          // simple: just the suite name
            {                       // object: custom display name + attr override
              "testsuite": "Power Rails",
              "name":      "Power Rails (High Voltage)",
              "attr":      { "supply_voltage": 5.0 }
            },
            {
              "testsuite": "Power Rails",
              "reps":      3         // repeat this suite 3 times (→ Rep#1, Rep#2, Rep#3)
            }
          ]
        }
      ]
    }
  ]
}
```

### Suite path files

For large projects, a test suite can live in its own JSON file and be referenced by path:

```jsonc
// duts.json
"testsuites": [
  { "path": "./suites/power_rails.json" }
]
```

```jsonc
// suites/power_rails.json
{
  "name": "Power Rails",
  "module": "tests.power_tests",
  "testcases": [...]
}
```

---

## 6. Test Programs and Test Suites

### Programs

A program selects an ordered subset of a DUT's suites, optionally customising them:

```jsonc
"programs": [
  {
    "name": "Quick Sanity",
    "testsuites": ["Power Rails"]   // single suite
  },
  {
    "name": "Full Production",
    "testsuites": [
      "Power Rails",
      "Communication",
      "Calibration"
    ]
  }
]
```

The same suite can appear multiple times in one program, with different `attr` overrides or repeated via `reps`.

### Suite repetitions

```jsonc
{ "testsuite": "Power Rails", "reps": 5 }
// Generates: Power Rails Rep#1, Power Rails Rep#2, … Rep#5
// Each repetition is independent in the results table.
```

---

## 7. Attributes (attr)

Attributes are arbitrary key-value pairs that flow down through the hierarchy and are merged at each level, with more specific levels winning:

```
test-case attr  <  suite attr  <  program attr  <  per-program ts_attr override
                                                  (+ user edits in UI at runtime)
```

Inside `_execute()`, read attributes from `config.attr`:

```python
def _execute(self, config: TestConfig, assets: dict) -> float:
    fw_version = config.attr.get("fw_version", "unknown")
    supply_v   = config.attr.get("supply_voltage", 3.3)
    ...
```

### Runtime attribute editing

If `attr_schema` is defined on the program, a collapsible form appears in the dashboard UI. The operator can change attribute values before running. Those changes propagate to all tests in the program via the merge chain.

```jsonc
"attr_schema": {
  "type": "object",
  "properties": {
    "fw_version": {
      "type": "string",
      "description": "Firmware version to flash before test"
    },
    "enable_extra_checks": {
      "type": "boolean",
      "description": "Run extended verification steps"
    }
  }
}
```

---

## 8. Skip / Infoonly

Both are set in `duts.json` per test case and can be changed live in the UI.

| Setting | Behaviour |
|---|---|
| `"skip": true` | Test is skipped (result = SKIPPED). Does not affect other tests. |
| `"infoonly": true` | Test always evaluates to INFOONLY regardless of value vs tolerance. Useful for measurements that are logged but not gating. |

When a setup test case fails:
- All test cases in that suite are automatically skipped (result = SKIPPED with a comment).
- Cleanup still runs.

When the DUT-level setup fails:
- Every test suite and all its tests are skipped.

---

## 9. Programmatic Control (no UI)

Set `ui=False` to use the tester from a script or CI pipeline:

```python
tester = MyTester(ui=False)

# Optional: configure a specific DUT and program
tester.select_dut("Board Rev A")
tester.select_program("Production")

# Optional: set runtime attributes
tester.run_attr["fw_version"] = "2.0.1"

# Run synchronously
tester.run()
tester.wait_for_test_end()

# Inspect results
for result in tester.test_run.test_results:
    print(result.name, result.result.name, result.value)
```

The framework also exposes a REST endpoint for external automation. POST to `/req/` with a JSON body:

```json
{ "cmd": "run", "dut": "Board Rev A", "program": "Production", "attr": {"fw_version": "2.0.1"} }
```

Returns `200` with a message, or `500` with an error description.

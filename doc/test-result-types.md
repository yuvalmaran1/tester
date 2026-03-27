# Test Result Types

The framework has five built-in result types. Each pairs an abstract `TestCase` subclass (which you inherit from) with a `TestResult` subclass (which handles evaluation and serialisation).

## Quick Reference

| Type | Import from | `_execute()` returns | Tolerance keys |
|---|---|---|---|
| Numeric | `tester.TestResults.NumericTestResult` | `float` / `int` | `min`, `max` |
| String | `tester.TestResults.StringTestResult` | `str` | `expected` |
| Bool | `tester.TestResults.BoolTestResult` | `bool` | `expected` |
| PassFail | `tester.TestResults.PassFailTestResult` | `TestResult.TestEval` | _(none)_ |
| Numeric2d | `tester.TestResults.Numeric2dTestResult` | `{"x": [...], "y": [...]}` | `min`, `max` |

---

## Numeric

Measures a single number against a min/max band.

**Pass condition:** `min <= value <= max`

```python
from tester.TestResults.NumericTestResult import NumericTestCase
from tester.TestConfig import TestConfig

class SupplyVoltageTest(NumericTestCase):
    def _execute(self, config: TestConfig, assets: dict) -> float:
        return assets["dmm"].measure_dc_voltage()
```

`duts.json` tolerance:
```json
{ "tolerance": { "min": 3.2, "max": 3.4 }, "unit": "V" }
```

The UI and report show Min, Value, Max columns with the unit.

---

## String

Compares a string to an exact expected value.

**Pass condition:** `value == expected`

```python
from tester.TestResults.StringTestResult import StringTestCase

class FirmwareVersionTest(StringTestCase):
    def _execute(self, config, assets) -> str:
        return assets["device"].read_fw_version()
```

`duts.json` tolerance:
```json
{ "tolerance": { "expected": "2.1.0" } }
```

The Min and Max columns in the UI both show the expected string; Value shows the measured string.

---

## Bool

Checks that a boolean equals an expected value.

**Pass condition:** `value == expected`

```python
from tester.TestResults.BoolTestResult import BoolTestCase

class SelfTestPassedTest(BoolTestCase):
    def _execute(self, config, assets) -> bool:
        return assets["device"].run_self_test()
```

`duts.json` tolerance:
```json
{ "tolerance": { "expected": true } }
```

---

## PassFail

For tests where you determine pass/fail yourself — no measured value.

**Pass condition:** return `TestResult.TestEval.PASS`

```python
from tester.TestResults.PassFailTestResult import PassFailTestCase
from tester.TestResult import TestResult

class FlashFirmwareTest(PassFailTestCase):
    def _execute(self, config, assets) -> TestResult.TestEval:
        ok = assets["flasher"].flash(config.attr.get("fw_path"))
        return TestResult.TestEval.PASS if ok else TestResult.TestEval.FAIL
```

`duts.json` — no tolerance needed:
```json
{ "name": "Flash Firmware", "test": "FlashFirmwareTest" }
```

**Also used for setup and cleanup** — return `PASS` to let subsequent tests run, anything else to skip them.

---

## Numeric2d

Measures an X-Y curve against per-point or uniform min/max tolerances. Automatically renders an interactive plot in the dashboard and in the HTML report.

**Pass condition:** every Y point is within `[min, max]` at that X position.

```python
from tester.TestResults.Numeric2dTestResult import Numeric2dTestCase
import numpy as np

class FrequencyResponseTest(Numeric2dTestCase):
    def _execute(self, config, assets) -> dict:
        freqs, gains = assets["vna"].sweep(start=1e3, stop=1e6, points=100)
        return {"x": freqs.tolist(), "y": gains.tolist()}
```

`duts.json` tolerance — **uniform bounds**:
```json
{
  "tolerance": { "min": -3.0, "max": 3.0 },
  "unit": "dB",
  "x_unit": "Hz"
}
```

`duts.json` tolerance — **shaped bounds** (piecewise linear, interpolated):
```json
{
  "tolerance": {
    "min": { "x": [0, 1000, 5000], "y": [-1.0, -2.0, -3.0] },
    "max": { "x": [0, 1000, 5000], "y": [ 1.0,  2.0,  3.0] }
  },
  "unit": "dB",
  "x_unit": "Hz"
}
```

The `unit` field labels the Y axis; `x_unit` labels the X axis. Both appear in the report plot.

---

## Result Evaluation States

All result types share the same evaluation enum:

| State | Meaning |
|---|---|
| `PASS` | Value within tolerance |
| `FAIL` | Value outside tolerance |
| `ERROR` | `_execute()` raised an exception, or returned the wrong type |
| `SKIPPED` | Test was skipped (setup failed, or operator disabled it) |
| `INFOONLY` | `infoonly: true` in `duts.json` — always this state regardless of value |
| `ABORTED` | Run was stopped by the operator mid-execution |
| `UNKNOWN` | Not yet executed |

Overall run result is the worst state across all tests (ABORTED > FAIL > ERROR > PASS).

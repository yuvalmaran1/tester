# Utilities

These helpers are available inside `_execute()` on any test case, or anywhere you have access to the `Tester` instance.

---

## Dialogs

`TestDialog` is a singleton that displays a modal dialog in the web UI and **blocks the test thread** until the operator responds (or it times out).

### Basic usage

```python
from tester.TestUtil import TestDialog

class InspectBoardTest(PassFailTestCase):
    def _execute(self, config, assets) -> TestResult.TestEval:
        # Block until operator clicks OK or Cancel (30-second timeout)
        response = self.dialog.display(
            title="Visual Inspection",
            text="Inspect the board for physical damage. Is it acceptable?",
            responses=[TestDialog.Response.Yes, TestDialog.Response.No],
            timeout=60,
        )
        if response == TestDialog.Response.Yes.name:
            return TestResult.TestEval.PASS
        return TestResult.TestEval.FAIL
```

`self.dialog` is available because `Tester` stores the singleton as `self.dialog`.

### With a form (dynamic input)

Pass a [JSON Schema](https://json-schema.org/) to render a form inside the dialog. The filled-in values are returned alongside the button response:

```python
schema = {
    "type": "object",
    "properties": {
        "serial_number": { "type": "string", "description": "Scanned serial number" },
        "visual_ok":     { "type": "boolean", "description": "Board passes visual inspection" }
    }
}

response = self.dialog.display(
    title="Scan Serial Number",
    text="Scan the barcode on the board, then confirm visual inspection.",
    schema=schema,
    defaults={"visual_ok": True},
    responses=[TestDialog.Response.Ok, TestDialog.Response.Cancel],
    timeout=120,
)
```

The return value is the button name (a string: `"Ok"`, `"Cancel"`, `"Yes"`, `"No"`).

To access the form data, use `self.dialog.response_data` after `display()` returns.

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `title` | `str` | `""` | Dialog heading |
| `text` | `str` | `""` | Instructional text shown to the operator |
| `schema` | `dict` | `{}` | JSON Schema for the embedded form (empty = no form) |
| `defaults` | `dict` | `{}` | Pre-filled values for the form |
| `responses` | `list[Response]` | `[Ok]` | Buttons to show |
| `timeout` | `int` | `30` | Seconds before auto-closing (0 = no timeout) |

A progress bar in the dialog counts down the timeout.

### Available response values

```python
TestDialog.Response.Ok
TestDialog.Response.Cancel
TestDialog.Response.Yes
TestDialog.Response.No
```

---

## File Attachments

`TestAttachment` is a singleton that bundles files into a zip archive stored with the run. The archive appears as a download link in the HTML report.

### Attach a file from disk

```python
class SaveWaveformTest(NumericTestCase):
    def _execute(self, config, assets) -> float:
        waveform_path = assets["scope"].save_screenshot("/tmp/waveform.png")
        self.attachment.attach_file(waveform_path)
        return assets["scope"].measure_peak()
```

### Attach data from memory

```python
import json

class ConfigDumpTest(PassFailTestCase):
    def _execute(self, config, assets) -> TestResult.TestEval:
        cfg = assets["device"].read_config()
        self.attachment.attach_buffer(
            json.dumps(cfg, indent=2),
            file_name="device_config.json"
        )
        return TestResult.TestEval.PASS
```

### Notes

- `self.attachment` is available on every `TestCase` via the `Tester` singleton.
- All attachments from all test cases in a run are combined into a single `attachments.zip`.
- The zip is embedded as a base64 data-URI in the report, so the report is fully self-contained.

---

## Comments

Any test case can attach a text comment to its result. Comments appear in the results table and in reports.

```python
def _execute(self, config, assets) -> float:
    value = assets["dmm"].measure()
    if value > 3.3:
        self.set_comment(f"High reading: {value:.4f}V — check capacitor C12")
    return value
```

Comments are also set automatically when a test is skipped because the operator disabled it ("Skipped by user") or because a setup failed.

---

## Logging

The framework uses a singleton logger accessible everywhere. Inside test cases you can write to it directly:

```python
from tester.TestLogger import TestLogger

class MyTest(NumericTestCase):
    def _execute(self, config, assets) -> float:
        TestLogger().info("Starting voltage measurement")
        v = assets["dmm"].measure()
        TestLogger().debug(f"Raw ADC reading: {v}")
        return v
```

Log messages appear live in the **Framework Log** modal in the UI (click the floating button at the bottom right of the dashboard). They are also stored with the run and embedded as a downloadable `tester.log` in the HTML report.

Log levels: `debug`, `info`, `warning`, `error` (standard Python logging levels).

---

## Aborting a Run

To stop the entire run from inside a test case (e.g. critical failure), raise `AbortRunException`:

```python
from tester.TestUtil import AbortRunException

class CriticalPowerTest(PassFailTestCase):
    def _execute(self, config, assets) -> TestResult.TestEval:
        if not assets["psu"].is_safe():
            raise AbortRunException("PSU over-current — aborting run")
        return TestResult.TestEval.PASS
```

This marks the current test as ABORTED and skips all remaining tests. The run result will be ABORTED.

The operator can also click **Stop** in the UI at any time, which injects `AbortRunException` into the running thread.

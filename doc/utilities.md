# Utilities

These helpers are available inside `_execute()` on any test case, or anywhere you have access to the `Tester` instance.

---

## Dialogs

`TestDialog` is a singleton that displays a modal dialog in the web UI. It supports both blocking prompts and non-blocking, multi-stage workflows.

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
        if (response or {}).get("rsp") == TestDialog.Response.Yes.name:
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

The return value is a response object such as `{"rsp": "Ok"}`. The submitted form values are available through `self.dialog.response_data`.

### Non-blocking workflow

`display_non_blocking()` returns immediately. Operator responses are recorded without hiding the dialog, allowing a test to change the instructions, remove buttons, and report operation progress before explicitly closing it.

```python
dialog = self.dialog.display_non_blocking(
    title="Manual connection",
    text="Connect the fixture, then press Done.",
    responses=[TestDialog.Response.Ok, TestDialog.Response.Cancel],
)

# The test can continue polling hardware while the dialog remains interactive.
while True:
    response = dialog.wait_for_response(timeout=0.1)
    if response is not None:
        break
    assets["fixture"].poll()

if response.get("rsp") == TestDialog.Response.Cancel.name:
    dialog.close()
    return TestResult.TestEval.FAIL

dialog.update(text="Programming device...", responses=[], progress=0)
for progress in assets["programmer"].program_with_progress():
    dialog.update(progress=progress)

dialog.update(text="Programming complete", progress=100)
dialog.close()
return TestResult.TestEval.PASS
```

The non-blocking methods are:

| Method | Description |
|---|---|
| `display_non_blocking(...)` | Opens the dialog and returns the `TestDialog` immediately |
| `wait_for_response(timeout=None, clear=True)` | Optionally waits for the next response without hiding the dialog |
| `update(...)` | Changes title, text, schema, defaults, buttons, or progress in place |
| `close()` | Explicitly hides the dialog |

`response` and `response_data` always contain the most recently submitted values.

See `InteractiveProgrammingTest` in
`example_tester/tests/programming_tests.py` for an executable example that
waits for manual preparation, keeps the dialog open, and reports programming
progress before closing it.

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `title` | `str` | `""` | Dialog heading |
| `text` | `str` | `""` | Instructional text shown to the operator |
| `schema` | `dict` | `{}` | JSON Schema for the embedded form (empty = no form) |
| `defaults` | `dict` | `{}` | Pre-filled values for the form |
| `responses` | `list[Response]` | `[Ok]` | Buttons to show |
| `timeout` | `int` | `30` | Seconds before blocking `display()` returns (0 = wait indefinitely) |

For blocking dialogs, the progress bar represents elapsed timeout. For non-blocking dialogs, pass `progress` to `update()` to control it explicitly.

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

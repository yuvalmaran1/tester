# Reports

Reports are self-contained HTML files — they embed all CSS, JavaScript (Plotly), images, and download attachments as base64 data-URIs. A report file can be emailed or archived and opened without a network connection.

---

## Generating a Report

### From the UI

After a run completes the **↓ Report** button appears in the dashboard control bar. Clicking it downloads the report for the most recently completed run.

On the **Runs** page (`/results`), every row has a view and a download button. View opens the report in a new browser tab; Download saves it locally.

### Programmatically

```python
from tester.TestReport import TestReport

# If you have a TestRun object (e.g. after calling tester.wait_for_test_end()):
report = TestReport(tester.test_run)
html_string = report.generate()
with open("./my_report.html", "w", encoding="utf-8") as f:
    f.write(html_string)

# Or save directly:
report = TestReport(tester.test_run, path="./my_report.html")
report.generate()
```

### From the database

```python
from tester.TestDB import TestDB
from tester.TestReport import TestReport

db = TestDB("./results.db")
run = db.get_run(run_id=42)
html = TestReport(run).generate()
```

---

## Report Contents

### Header

The report header shows:
- Framework name and the tester application version
- Framework (library) version
- Date and time the report was generated

### Summary statistics

Six stat cards across the top:
- **Overall Result** — PASS / FAIL / ERROR / ABORTED (colour-coded)
- **Tests Executed** — total count
- **Passed** — count of PASS results
- **Failed** — count of FAIL results
- **Errors** — count of ERROR results
- **Duration** — HH:MM:SS elapsed time

### Device Under Test

DUT name, description, product ID, and the DUT image (embedded as base64; falls back to the framework default image if not found).

### Test Program

Program name, description, start time, and duration. If the operator modified skip states before running, a **Modified** badge appears next to the program name.

### Program Attributes

If the program has `attr` values, they are shown in a two-column table (Attribute / Value). These represent the parameter values that were active during the run (e.g. firmware version under test).

### Detailed Test Results

A table with one row per test case:

| Column | Description |
|---|---|
| **Time** | Elapsed time from run start |
| **Suite** | Test suite name |
| **Name** | Test case name |
| **Min** | Lower tolerance bound (or expected value for string/bool) |
| **Value** | Measured value |
| **Max** | Upper tolerance bound |
| **Unit** | Engineering unit |
| **Result** | Colour-coded badge |
| **Comment** | Free-text comment from the test case |

For **Numeric2d** test cases, an interactive Plotly chart is rendered inline in the row immediately below the test result. The chart shows the measured curve (green) against min tolerance (blue dashed) and max tolerance (red dashed), with a shaded band between the limits.

### Attachments section

Download buttons are shown for:
- **tester.log** — the full framework log for this run (always present)
- **attachments.zip** — any files attached via `TestAttachment` (only present if attachments exist)

Both are embedded as base64 data-URIs so they download without a server.

---

## Report Appearance

Reports use a dark colour scheme that mirrors the web UI:

| Result | Colour |
|---|---|
| PASS | Green `#10b981` |
| FAIL | Red `#ef4444` |
| ERROR | Amber `#f59e0b` |
| INFOONLY | Blue `#60a5fa` |
| SKIPPED | Slate `#64748b` |
| ABORTED | Purple `#a78bfa` |

The report is fully responsive and renders on mobile screens.

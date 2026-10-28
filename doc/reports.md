# Reports

Reports can be generated as self-contained HTML or as PDF. HTML reports include interactive Plotly charts and embedded attachment downloads. PDF reports provide a portable, printable summary with traceability metadata, program attributes, and the complete result table.

---

## Generating a Report

### From the UI

After a run completes, **HTML** and **PDF** download buttons appear in the dashboard control bar.

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

# Generate PDF bytes:
pdf_bytes = TestReport(tester.test_run).generate_pdf()
with open("./my_report.pdf", "wb") as f:
    f.write(pdf_bytes)
```

### From the database

```python
from tester.TestDB import TestDB
from tester.TestReport import TestReport

db = TestDB("./results.db")
run = db.get_run(run_id=42)
html = TestReport(run).generate()
pdf = TestReport(run).generate_pdf()
```

The HTTP API exposes `/get_report_pdf` for the latest run and `/generate_report_pdf/<id>` for a historical run.

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

The interactive HTML report uses the web UI's dark colour scheme. The PDF uses the same information hierarchy in a light, print-oriented layout: report header, six summary cards, side-by-side DUT and program panels, program attributes, colour-coded results, and page footers with run identity and page number.

Result colours are preserved in both formats:

| Result | Colour |
|---|---|
| PASS | Green `#10b981` |
| FAIL | Red `#ef4444` |
| ERROR | Amber `#f59e0b` |
| INFOONLY | Blue `#60a5fa` |
| SKIPPED | Slate `#64748b` |
| ABORTED | Purple `#a78bfa` |

The HTML report is fully responsive and renders on mobile screens. The PDF uses landscape A4 pages for a readable complete result table.

# User Interface

The web UI is served by the Flask backend on `http://localhost:5050`. It has three pages reachable via the top navigation bar.

---

## Dashboard (`/`)

The main operator screen. Used to configure and run tests, and monitor live results.

### Control bar

At the top of the page:

**DUT and Program selectors** — Drop-downs to choose which device type to test and which test program to run. Both are disabled while a run is in progress.

**Run / Stop button** — Starts the selected program. Turns into a Stop button while running; clicking Stop injects a graceful abort that marks the current test as ABORTED and skips the rest.

**Reload button** (circular arrow) — Re-reads `duts.json` and reinitialises all DUT definitions without restarting the server. Useful when editing test configuration during development. Disabled while a run is active.

**Report button** — Appears after a run completes. Downloads the HTML report for the most recent run. (See [Reports](reports.md).)

**Statistics row** — Live counters for Done/Total, Pass, Fail, Error, Skipped, Aborted, with a progress bar and elapsed time. The status text below the bar shows the name of the currently executing test case.

**Program Attributes panel** (collapsible) — If the selected program defines an `attr_schema`, a form appears here. The operator can change attribute values (e.g. firmware version, test mode flags) before pressing Run. Changes take effect on the next run. The panel is read-only while a run is in progress.

### Results table

Below the control bar, a table shows one row per test case in the current program. Columns:

| Column | Description |
|---|---|
| **Run** (checkbox) | Enable or disable this test case. Toggling a setup/cleanup also enables/disables all tests in that suite. Grey while a run is active. |
| **Time** | Elapsed time from run start when the test completed. Blank until the test executes. |
| **Suite** | The test suite this test belongs to. |
| **Test Name** | The test case name. A pulsing dot marks the currently running test. |
| **Min / Value / Max** | Tolerance bounds and measured value. For Numeric2d tests these show `-----` / `--See Plot--` / `-----`. |
| **Unit** | Engineering unit. |
| **Result** | Colour-coded badge: PASS (green), FAIL (red), ERROR (amber), SKIPPED (grey), INFOONLY (blue), ABORTED (purple). |
| **Comment** | Any comment set by the test case. |

For Numeric2d tests, an interactive chart is rendered in an expandable row directly below the test result, showing the measured curve against min/max tolerance bands.

### Framework Log modal

The floating button (bottom right) opens the log modal. It shows the live framework log — all `TestLogger` output from the current (or last) run, streaming in real time. Useful for debugging test cases without needing to attach a terminal. The log auto-scrolls to the bottom as new entries arrive.

### Test Dialog

If a test case calls `self.dialog.display(...)`, a modal appears on top of the dashboard. The operator must respond before the test can continue. The dialog can contain instructional text, a dynamic form (JSON Schema rendered by JSONForms), a countdown progress bar, and configurable buttons (Ok, Cancel, Yes, No). Closing the browser tab or losing connectivity does not close the dialog — it times out automatically.

### Offline overlay

If the browser loses connection to the backend, a full-screen overlay appears ("Backend Disconnected") and blocks interaction until the connection is restored.

---

## Runs (`/results`)

A historical view of all recorded test runs, sorted newest first.

**Table columns:**

| Column | Description |
|---|---|
| — | Expand button — opens the full results table for that run inline (not currently implemented; expands are shown in reports). |
| **ID** | Auto-incremented run ID from the database. |
| **Device** | DUT name. |
| **Program** | Program name. A "Modified" badge appears if the operator changed skip states before running. |
| **Start Time** | Date and time the run started. |
| **Duration** | Total run time (HH:MM:SS). |
| **Result** | Colour-coded badge for the overall run outcome. |

Each row has two icon buttons:
- **View Report** — Opens the HTML report for that run in a new browser tab.
- **Download Report** — Downloads the HTML report as a self-contained file.

Click **Refresh** (top right) to reload the list.

---

## Tests (`/test-query`)

A cross-run analysis view for querying and visualising historical test results for specific test cases.

### Filter panel

Select which data to retrieve using multi-select drop-downs:

| Filter | Description |
|---|---|
| **Test Names** | One or more test case names (populated from the database). At least one is required to run a query. |
| **Programs** | Limit results to specific programs. |
| **Devices Under Test** | Limit results to specific DUTs. |
| **Results** | Limit to specific outcomes (PASS, FAIL, ERROR, SKIPPED, ABORTED). |
| **Start Date / End Date** | Date range filter. |

Click **Query Results** to fetch matching records. Click **Clear** to reset all filters.

### Histograms

For each selected test name, a histogram is rendered above the results table (for numeric, bool, string, and passfail types). The histogram shows the distribution of outcomes or values across all matching runs — useful for spotting drift, systematic failures, or margin issues.

### Results table

Below the histograms, a flat table lists every individual test result matching the filters, with columns for Run ID, Program, DUT, Suite, Test Name, Result, Value, Unit, and Timestamp. Numeric2d results include the interactive plot inline.

Results are excluded from setup and cleanup test cases — only regular test cases are shown here.

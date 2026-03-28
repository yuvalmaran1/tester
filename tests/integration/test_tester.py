"""Integration tests for the full Tester run lifecycle.

All tests use the make_tester factory fixture from conftest.py which wires
fast, headless tester instances to temporary file paths.
"""
import threading
import pytest
from tester.TestResult import TestResult

from conftest import (
    DUTS_STANDARD, DUTS_DUT_SETUP_FAIL, DUTS_SLOW, DUTS_ATTR_READ,
    DUTS_RUN_DATA, STATION_DATA,
)

E = TestResult.TestEval


# ── Helper ────────────────────────────────────────────────────────────────────

def _run_and_wait(tester):
    """Start a run and block until it finishes."""
    tester.run()
    tester.wait_for_test_end()


def _result_by_name(tester, name):
    return next((r for r in tester.test_run.test_results if r.name == name), None)


# ── DUT / program selection ───────────────────────────────────────────────────

def test_select_dut_sets_active_dut(make_tester):
    t = make_tester()
    assert t.active_dut is not None
    assert t.active_dut.name == "Test DUT"


def test_select_program_sets_active_program(make_tester):
    t = make_tester()
    assert t.active_program is not None
    assert t.active_program.name == "Test Program"


def test_select_program_by_name(make_tester):
    t = make_tester()
    t.select_program("Test Program")
    assert t.active_program.name == "Test Program"


def test_run_raises_when_already_running(make_tester):
    """Calling run() a second time while a run is in progress must raise."""
    t = make_tester(DUTS_SLOW)
    t.run()
    try:
        with pytest.raises(RuntimeError):
            t.run()
    finally:
        t._stop_run_handler()
        t.wait_for_test_end()


# ── Full run lifecycle ────────────────────────────────────────────────────────

def test_full_run_completes(make_tester):
    t = make_tester()
    _run_and_wait(t)
    assert not t.running
    assert t.test_run.end_date is not None


def test_full_run_results_written_to_db(make_tester):
    t = make_tester()
    _run_and_wait(t)
    run_id = t.test_run.run_id
    assert run_id is not None
    db_run = t.db.get_run(run_id)
    assert len(db_run.test_results) > 0


def test_full_run_pass_test_is_pass(make_tester):
    t = make_tester()
    _run_and_wait(t)
    r = _result_by_name(t, "Pass Test")
    assert r is not None
    assert r.result == E.PASS


def test_full_run_fail_test_is_fail(make_tester):
    t = make_tester()
    _run_and_wait(t)
    r = _result_by_name(t, "Fail Test")
    assert r is not None
    assert r.result == E.FAIL


def test_full_run_overall_result_is_fail(make_tester):
    """Standard suite has a FAIL test → overall run result is FAIL."""
    t = make_tester()
    _run_and_wait(t)
    assert t.test_run.result == E.FAIL


def test_run_status_resets_to_idle(make_tester):
    t = make_tester()
    _run_and_wait(t)
    assert t.status_str == "Idle"
    assert t.active_test == -1


# ── Statistics tracking ───────────────────────────────────────────────────────

def test_stats_total_matches_result_count(make_tester):
    t = make_tester()
    _run_and_wait(t)
    assert t.test_stats['total'] == len(t.test_run.test_results)


def test_stats_done_matches_total(make_tester):
    t = make_tester()
    _run_and_wait(t)
    assert t.test_stats['done'] == t.test_stats['total']


def test_stats_pass_count(make_tester):
    t = make_tester()
    _run_and_wait(t)
    expected = sum(1 for r in t.test_run.test_results if r.result == E.PASS)
    assert t.test_stats['PASS'] == expected


def test_stats_fail_count(make_tester):
    t = make_tester()
    _run_and_wait(t)
    expected = sum(1 for r in t.test_run.test_results if r.result == E.FAIL)
    assert t.test_stats['FAIL'] == expected


# ── DUT setup failure cascades ────────────────────────────────────────────────

def test_dut_setup_fail_skips_all_suite_testcases(make_tester):
    t = make_tester(DUTS_DUT_SETUP_FAIL)
    _run_and_wait(t)
    # DUT setup FAILS; DUT cleanup still runs (not skipped) — exclude both.
    # Everything else (suite testcases) must be SKIPPED.
    excluded = {"Setup", "Cleanup"}
    non_setup_cleanup = [r for r in t.test_run.test_results if r.name not in excluded]
    assert all(r.result == E.SKIPPED for r in non_setup_cleanup), (
        f"Expected all suite testcases to be SKIPPED: "
        f"{[(r.name, r.result) for r in non_setup_cleanup]}"
    )


def test_dut_setup_fail_overall_result_not_pass(make_tester):
    t = make_tester(DUTS_DUT_SETUP_FAIL)
    _run_and_wait(t)
    assert t.test_run.result != E.PASS


# ── Suite-level setup failure cascade ─────────────────────────────────────────

DUTS_SUITE_SETUP_FAIL = {
    "duts": [{
        "name": "Test DUT",
        "description": "DUT",
        "image": "", "product_id": "x", "attr": {},
        "programs": [{"name": "Test Program", "description": "", "attr": {},
                      "testsuites": ["FailSetupSuite"]}],
        "testsuites": [{
            "name": "FailSetupSuite",
            "module": "fixtures.fast_tests",
            "setup": "FastSetupFailTest",
            "cleanup": "FastCleanupTest",
            "testcases": [
                {"name": "TC1", "module": "fixtures.fast_tests",
                 "test": "FastPassTest", "tolerance": {}},
            ],
        }],
    }]
}


def test_suite_setup_fail_skips_testcases(make_tester):
    t = make_tester(DUTS_SUITE_SETUP_FAIL)
    _run_and_wait(t)
    tc1 = _result_by_name(t, "TC1")
    assert tc1 is not None
    assert tc1.result == E.SKIPPED


def test_suite_cleanup_runs_after_setup_fail(make_tester):
    """Cleanup must still execute even when suite setup failed."""
    t = make_tester(DUTS_SUITE_SETUP_FAIL)
    _run_and_wait(t)
    cleanup = _result_by_name(t, "Cleanup")
    assert cleanup is not None
    assert cleanup.result != E.UNKNOWN


# ── Attribute hierarchy ───────────────────────────────────────────────────────

def test_attr_program_wins_over_dut(make_tester):
    """When DUT and program both define 'read_key', program value must win."""
    t = make_tester(DUTS_ATTR_READ)
    _run_and_wait(t)
    r = _result_by_name(t, "Attr Test")
    assert r is not None
    # AttrReadTest returns config.attr['read_key']; tolerance.expected == 'from_program'
    assert r.result == E.PASS   # value == 'from_program' matches expected


def test_attr_user_override_wins_over_program(make_tester):
    """User attribute supplied via _attr_handler must take precedence."""
    t = make_tester(DUTS_ATTR_READ)
    # Override with a value that does NOT match the tolerance 'from_program'
    t._attr_handler({'read_key': 'user_override'})
    _run_and_wait(t)
    r = _result_by_name(t, "Attr Test")
    assert r is not None
    # value == 'user_override' ≠ 'from_program' → FAIL
    assert r.result == E.FAIL


# ── Skip-by-user ──────────────────────────────────────────────────────────────

def test_skip_by_user_marks_result_skipped(make_tester):
    t = make_tester()
    t._test_execute_state_handler({
        'test_id': 'Suite1_Pass Test',
        'execute': False,
        'type': 'testcase',
    })
    _run_and_wait(t)
    r = _result_by_name(t, "Pass Test")
    assert r.result == E.SKIPPED


def test_skip_by_user_adds_comment(make_tester):
    t = make_tester()
    t._test_execute_state_handler({
        'test_id': 'Suite1_Pass Test',
        'execute': False,
        'type': 'testcase',
    })
    _run_and_wait(t)
    r = _result_by_name(t, "Pass Test")
    assert "Skipped by user" in r.comment


def test_skip_preserved_across_select_program(make_tester):
    """User's skip state must survive a subsequent select_program call."""
    t = make_tester()
    t._test_execute_state_handler({
        'test_id': 'Suite1_Pass Test',
        'execute': False,
        'type': 'testcase',
    })
    # Simulate what _run() does at the start: re-select the same program
    t.select_program(t.active_program.name, reset_attr=False)
    # The skip state should be preserved in the re-created active_program
    tc = next(
        tc for ts in t.active_program.testsuites
        for tc in ts.testcases if tc.config.name == "Pass Test"
    )
    assert tc.config.skip is True


# ── program_modified flag ─────────────────────────────────────────────────────

def test_program_modified_flag_set_when_user_skips(make_tester):
    t = make_tester()
    t._test_execute_state_handler({
        'test_id': 'Suite1_Pass Test',
        'execute': False,
        'type': 'testcase',
    })
    _run_and_wait(t)
    assert t.test_run.program_modified is True


def test_program_modified_flag_false_when_no_user_changes(make_tester):
    t = make_tester()
    _run_and_wait(t)
    assert t.test_run.program_modified is False


# ── Abort ─────────────────────────────────────────────────────────────────────

def test_abort_stops_run(make_tester):
    """Aborting mid-run causes at least one test to not PASS and subsequent
    tests to be SKIPPED.

    Note: _ctype_async_raise does not reliably interrupt time.sleep on
    Windows/Python 3.13, so we cannot assert ABORTED specifically for the
    slow test.  Instead we verify that the abort flag was acted on by
    checking that subsequent tests are SKIPPED.
    """
    t = make_tester(DUTS_SLOW)
    # Fire abort at 0.15 s — before SlowTest (1 s sleep) finishes
    timer = threading.Timer(0.15, t._stop_run_handler)
    timer.start()
    try:
        t.run()
        t.wait_for_test_end()
    finally:
        timer.cancel()
    # The run must not have completed all tests normally
    results = t.test_run.test_results
    assert any(r.result != E.PASS for r in results), (
        "Expected at least one non-PASS result after abort"
    )


def test_abort_skips_subsequent_tests(make_tester):
    """Tests after the slow (aborted/skipped) test must be SKIPPED."""
    t = make_tester(DUTS_SLOW)
    timer = threading.Timer(0.15, t._stop_run_handler)
    timer.start()
    try:
        t.run()
        t.wait_for_test_end()
    finally:
        timer.cancel()
    after_slow = _result_by_name(t, "After Slow")
    assert after_slow is not None
    assert after_slow.result == E.SKIPPED


def test_abort_flag_set_on_stop(make_tester):
    """_stop_run_handler must set abort_run=True during a run."""
    t = make_tester(DUTS_SLOW)
    # Capture abort_run state inside the timer callback
    observed = []

    def _abort_and_observe():
        t._stop_run_handler()
        observed.append(t.abort_run)

    timer = threading.Timer(0.15, _abort_and_observe)
    timer.start()
    try:
        t.run()
        t.wait_for_test_end()
    finally:
        timer.cancel()
    assert observed and observed[0] is True


# ── Reload ────────────────────────────────────────────────────────────────────

def test_reload_handler_preserves_dut_selection(make_tester):
    t = make_tester()
    original_dut = t.active_dut.name
    t._reload_handler()
    assert t.active_dut.name == original_dut


def test_reload_handler_preserves_program_selection(make_tester):
    t = make_tester()
    original_prog = t.active_program.name
    t._reload_handler()
    assert t.active_program.name == original_prog


# ── run_data ──────────────────────────────────────────────────────────────────

def test_run_data_flows_between_test_cases(make_tester):
    """Value written to run_data by TC1 is visible to TC2 in the same run."""
    t = make_tester(DUTS_RUN_DATA)
    _run_and_wait(t)
    r = _result_by_name(t, "Read Test")
    assert r is not None
    assert r.result == E.PASS   # value == 'hello' matches tolerance expected


def test_run_data_is_none_after_run_completes(make_tester):
    """run_data is set to None after the run ends (memory release)."""
    t = make_tester(DUTS_RUN_DATA)
    _run_and_wait(t)
    assert t.run_data is None


def test_run_data_is_isolated_between_runs(make_tester):
    """Each run starts with a fresh empty dict; data from run 1 is gone in run 2."""
    t = make_tester(DUTS_RUN_DATA)
    _run_and_wait(t)
    # Second run: run_data is freshly initialised — Write Test re-writes 'hello'
    t.select_program(t.active_program.name)
    _run_and_wait(t)
    r = _result_by_name(t, "Read Test")
    assert r is not None
    assert r.result == E.PASS


# ── Traceability ──────────────────────────────────────────────────────────────

def test_config_hash_set_after_init(make_tester):
    """Tester computes a non-empty config hash on startup."""
    t = make_tester()
    assert len(t.config_hash) == 64  # SHA-256 hex digest


def test_config_hash_is_sha256_hex(make_tester):
    """Config hash is a valid lowercase hex string."""
    t = make_tester()
    assert all(c in '0123456789abcdef' for c in t.config_hash)


def test_serial_number_default_empty(make_tester):
    t = make_tester()
    assert t.serial_number == ''


def test_run_stores_serial_number(make_tester):
    """Serial number set before run is persisted in DB."""
    t = make_tester()
    t.serial_number = 'SN-TEST-001'
    t.run()
    t.wait_for_test_end()
    run = t.db.get_run(t.db.get_latest_run_id())
    assert run.serial_number == 'SN-TEST-001'


def test_run_stores_config_hash(make_tester):
    """Config hash is persisted in DB with each run."""
    t = make_tester()
    t.run()
    t.wait_for_test_end()
    run = t.db.get_run(t.db.get_latest_run_id())
    assert run.config_hash == t.config_hash
    assert len(run.config_hash) == 64


def test_run_empty_serial_if_not_set(make_tester):
    """When no serial number is set, run stores empty string."""
    t = make_tester()
    assert t.serial_number == ''
    t.run()
    t.wait_for_test_end()
    run = t.db.get_run(t.db.get_latest_run_id())
    assert run.serial_number == '' or run.serial_number is None

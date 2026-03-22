"""Integration tests for TestSuite.from_dict: loading, attr inheritance.

Note: Setup-fail cascade behaviour (setup FAIL → testcases skipped) is tested
in test_tester.py because it is implemented by RunExecutorMixin._execute_testsuite,
not by TestSuite itself.
"""
import sys
from pathlib import Path

# Ensure tests/fixtures is importable as "fixtures.*"
_TESTS_ROOT = str(Path(__file__).parent.parent)
if _TESTS_ROOT not in sys.path:
    sys.path.insert(0, _TESTS_ROOT)

from tester.TestSuite import TestSuite
from tester.TestResult import TestResult

E = TestResult.TestEval


def _suite(d, assets=None):
    return TestSuite.from_dict(d, assets or {}, debug_reload=False)


# ── Minimal suite descriptors ─────────────────────────────────────────────────

SUITE_FULL = {
    'name': 'FullSuite',
    'module': 'fixtures.fast_tests',
    'setup': 'FastSetupTest',
    'cleanup': 'FastCleanupTest',
    'testcases': [
        {'name': 'TC1', 'module': 'fixtures.fast_tests', 'test': 'FastPassTest', 'tolerance': {}},
        {'name': 'TC2', 'module': 'fixtures.fast_tests', 'test': 'FastFailTest', 'tolerance': {}},
    ],
}

SUITE_NO_SETUP_CLEANUP = {
    'name': 'BareSuite',
    'module': 'fixtures.fast_tests',
    'testcases': [
        {'name': 'TC1', 'module': 'fixtures.fast_tests', 'test': 'FastPassTest', 'tolerance': {}},
    ],
}

SUITE_WITH_ATTR = {
    'name': 'AttrSuite',
    'module': 'fixtures.fast_tests',
    'attr': {'suite_key': 'suite_val', 'shared': 'from_suite'},
    'setup': 'FastSetupTest',
    'cleanup': 'FastCleanupTest',
    'testcases': [
        {'name': 'TC1', 'module': 'fixtures.fast_tests', 'test': 'FastPassTest',
         'tolerance': {}, 'attr': {'tc_key': 'tc_val', 'shared': 'from_tc'}},
    ],
}


# ── Structure ─────────────────────────────────────────────────────────────────

def test_suite_name():
    assert _suite(SUITE_FULL).name == 'FullSuite'


def test_suite_has_setup_and_cleanup():
    ts = _suite(SUITE_FULL)
    assert ts.setup is not None
    assert ts.cleanup is not None


def test_suite_testcase_count():
    ts = _suite(SUITE_FULL)
    assert len(ts.testcases) == 2


def test_suite_without_setup_cleanup():
    ts = _suite(SUITE_NO_SETUP_CLEANUP)
    assert ts.setup is None
    assert ts.cleanup is None
    assert len(ts.testcases) == 1


# ── Module loading ────────────────────────────────────────────────────────────

def test_setup_correct_class_loaded():
    """Executing the setup must return PASS (FastSetupTest behaviour)."""
    ts = _suite(SUITE_FULL)
    ts.setup.execute()
    assert ts.setup.result.result == E.PASS


def test_testcase_classes_loaded():
    """First TC is FastPassTest → PASS; second is FastFailTest → FAIL."""
    ts = _suite(SUITE_FULL)
    ts.testcases[0].execute()
    ts.testcases[1].execute()
    assert ts.testcases[0].result.result == E.PASS
    assert ts.testcases[1].result.result == E.FAIL


# ── Attr inheritance ──────────────────────────────────────────────────────────

def test_suite_attr_flows_to_setup():
    ts = _suite(SUITE_WITH_ATTR)
    assert ts.setup.config.attr.get('suite_key') == 'suite_val'


def test_suite_attr_flows_to_cleanup():
    ts = _suite(SUITE_WITH_ATTR)
    assert ts.cleanup.config.attr.get('suite_key') == 'suite_val'


def test_suite_attr_flows_to_testcases():
    ts = _suite(SUITE_WITH_ATTR)
    assert ts.testcases[0].config.attr.get('suite_key') == 'suite_val'


def test_testcase_attr_merged_with_suite_attr():
    ts = _suite(SUITE_WITH_ATTR)
    # Both suite_key (from suite) and tc_key (from testcase) are present
    tc_attr = ts.testcases[0].config.attr
    assert tc_attr.get('suite_key') == 'suite_val'
    assert tc_attr.get('tc_key') == 'tc_val'


def test_testcase_attr_wins_over_suite_attr_for_same_key():
    """When suite and testcase define the same key, testcase wins (rightmost merge)."""
    ts = _suite(SUITE_WITH_ATTR)
    # In TestSuite.from_dict: tc_cfg.attr = s.attr | tc_cfg.attr  → tc wins
    assert ts.testcases[0].config.attr.get('shared') == 'from_tc'


# ── debug_reload ──────────────────────────────────────────────────────────────

def test_debug_reload_false_does_not_raise():
    """Sanity check that debug_reload=False still loads correctly."""
    ts = TestSuite.from_dict(SUITE_FULL, {}, debug_reload=False)
    assert ts.name == 'FullSuite'

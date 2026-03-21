"""Integration tests for TestCase: execute, skip, exception handling, abort."""
import pytest
from tester.TestCase import TestCase
from tester.TestConfig import TestConfig
from tester.TestResult import TestResult
from tester.TestResults.PassFailTestResult import PassFailTestCase
from tester.TestResults.NumericTestResult import NumericTestCase
from tester.TestResults.StringTestResult import StringTestCase
from tester.TestUtil import AbortRunException

E = TestResult.TestEval


# ── Concrete test case classes ────────────────────────────────────────────────

class PassCase(PassFailTestCase):
    def _execute(self, config, assets):
        return E.PASS


class FailCase(PassFailTestCase):
    def _execute(self, config, assets):
        return E.FAIL


class ErrorCase(PassFailTestCase):
    def _execute(self, config, assets):
        raise RuntimeError("deliberate error")


class AbortCase(PassFailTestCase):
    def _execute(self, config, assets):
        raise AbortRunException("abort")


class CommentCase(PassFailTestCase):
    def _execute(self, config, assets):
        self.set_comment("my comment")
        return E.PASS


class InfoonlyCase(NumericTestCase):
    """Returns 999.0 which is outside any sensible range — INFOONLY overrides."""
    def _execute(self, config, assets):
        return 999.0


class ExecutingFlagCapture(PassFailTestCase):
    """Records TestCase.is_executing() value during _execute."""
    captured: list = []

    def _execute(self, config, assets):
        ExecutingFlagCapture.captured.append(TestCase.is_executing())
        return E.PASS


# ── Helper ───────────────────────────────────────────────────────────────────

def _tc(cls, *, tolerance=None, infoonly=False, skip=False):
    cfg = TestConfig(attr={}, tolerance=tolerance or {}, infoonly=infoonly, skip=skip)
    return cls(cfg, {}, 'TestSuite')


# ── execute() result mapping ──────────────────────────────────────────────────

def test_execute_pass():
    tc = _tc(PassCase)
    tc.execute()
    assert tc.result.result == E.PASS


def test_execute_fail():
    tc = _tc(FailCase)
    tc.execute()
    assert tc.result.result == E.FAIL


def test_execute_exception_gives_error():
    tc = _tc(ErrorCase)
    tc.execute()
    assert tc.result.result == E.ERROR


def test_execute_exception_stores_message_in_comment():
    tc = _tc(ErrorCase)
    tc.execute()
    assert "deliberate error" in tc.result.comment


def test_execute_abort_exception_gives_aborted():
    tc = _tc(AbortCase)
    tc.execute()
    assert tc.result.result == E.ABORTED


# ── skip() ───────────────────────────────────────────────────────────────────

def test_skip_gives_skipped():
    tc = _tc(PassCase)
    tc.skip()
    assert tc.result.result == E.SKIPPED


def test_skip_sets_date():
    tc = _tc(PassCase)
    tc.skip()
    assert tc.result.date is not None


def test_skip_does_not_call_execute():
    """Skipping an error-raising test must not produce ERROR."""
    tc = _tc(ErrorCase)
    tc.skip()
    assert tc.result.result == E.SKIPPED


# ── set_comment() ────────────────────────────────────────────────────────────

def test_set_comment_persists():
    tc = _tc(PassCase)
    tc.set_comment("hello")
    assert tc.result.comment == "hello"


def test_set_comment_called_inside_execute():
    tc = _tc(CommentCase)
    tc.execute()
    assert tc.result.comment == "my comment"


# ── is_executing() class flag ─────────────────────────────────────────────────

def test_is_executing_true_during_execute():
    ExecutingFlagCapture.captured.clear()
    tc = _tc(ExecutingFlagCapture)
    tc.execute()
    assert True in ExecutingFlagCapture.captured


def test_is_executing_false_after_execute():
    tc = _tc(PassCase)
    tc.execute()
    assert not TestCase.is_executing()


# ── infoonly config flag ──────────────────────────────────────────────────────

def test_infoonly_overrides_out_of_range_value():
    tc = _tc(InfoonlyCase, tolerance={'min': 0.0, 'max': 1.0}, infoonly=True)
    tc.execute()
    assert tc.result.result == E.INFOONLY


# ── execute() sets date ───────────────────────────────────────────────────────

def test_execute_sets_result_date():
    tc = _tc(PassCase)
    tc.execute()
    assert tc.result.date is not None

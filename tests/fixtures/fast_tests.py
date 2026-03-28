"""Fast test case implementations for use in integration tests.

All test cases here complete instantly (no sleep) so that the test suite
runs quickly.  They are referenced by name in duts.json fixtures written
by conftest.py.
"""
import time

from tester.TestResult import TestResult
from tester.TestConfig import TestConfig
from tester.TestResults.PassFailTestResult import PassFailTestCase
from tester.TestResults.StringTestResult import StringTestCase
from tester.SNGenerator import SNGenerator


class FastPassTest(PassFailTestCase):
    """Immediately returns PASS."""
    def _execute(self, config: TestConfig, assets, run_data: dict) -> TestResult.TestEval:
        return TestResult.TestEval.PASS


class FastFailTest(PassFailTestCase):
    """Immediately returns FAIL."""
    def _execute(self, config: TestConfig, assets, run_data: dict) -> TestResult.TestEval:
        return TestResult.TestEval.FAIL


class FastErrorTest(PassFailTestCase):
    """Raises an exception so the framework records ERROR."""
    def _execute(self, config: TestConfig, assets, run_data: dict) -> TestResult.TestEval:
        raise RuntimeError("deliberate test error")


class FastSetupTest(PassFailTestCase):
    """Generic setup that always passes."""
    def _execute(self, config: TestConfig, assets, run_data: dict) -> TestResult.TestEval:
        return TestResult.TestEval.PASS


class FastCleanupTest(PassFailTestCase):
    """Generic cleanup that always passes."""
    def _execute(self, config: TestConfig, assets, run_data: dict) -> TestResult.TestEval:
        return TestResult.TestEval.PASS


class FastSetupFailTest(PassFailTestCase):
    """Setup that always fails — used to test cascade-skip behavior."""
    def _execute(self, config: TestConfig, assets, run_data: dict) -> TestResult.TestEval:
        return TestResult.TestEval.FAIL


class AttrReadTest(StringTestCase):
    """Returns the value of config.attr['read_key'] so attr-hierarchy tests can
    verify the correct value flowed through the merge chain."""
    def _execute(self, config: TestConfig, assets, run_data: dict) -> str:
        return str(config.attr.get('read_key', 'missing'))


class RunDataWriteTest(PassFailTestCase):
    """Writes a known value into run_data so tests can verify it was threaded through."""
    def _execute(self, config: TestConfig, assets, run_data: dict) -> TestResult.TestEval:
        run_data['written'] = 'hello'
        return TestResult.TestEval.PASS


class RunDataReadTest(StringTestCase):
    """Reads run_data['written'] — used to verify data flows between test cases."""
    def _execute(self, config: TestConfig, assets, run_data: dict) -> str:
        return run_data.get('written', 'missing')


class SequentialSNGenerator(SNGenerator):
    """Generates serial numbers SN-0001, SN-0002, … for use in tests."""

    def __init__(self, assets):
        super().__init__(assets)
        self._counter = 0

    def generate(self) -> str:
        self._counter += 1
        return f"SN-{self._counter:04d}"


class SlowTest(PassFailTestCase):
    """Sleeps long enough that an abort signal can be delivered before the test
    finishes, but short enough that the test suite does not take forever if
    _ctype_async_raise does not interrupt time.sleep (Windows/Python 3.13).
    Used exclusively in abort-run tests."""
    def _execute(self, config: TestConfig, assets, run_data: dict) -> TestResult.TestEval:
        time.sleep(1)
        return TestResult.TestEval.PASS

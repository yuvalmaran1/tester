"""
generic_tests.py
================
DUT-level and suite-level setup / cleanup test cases.

These run before and after every test suite (and the whole run) to power-cycle
the DUT and verify it is responsive before measurements begin.
"""
from tester.TestResult import TestResult
from tester.TestConfig import TestConfig
from tester.TestResults.PassFailTestResult import PassFailTestCase
from tester.TestUtil import AbortRunException
from tester.TestLogger import TestLogger


class DutSetup(PassFailTestCase):
    """Enable the PSU and wait for the DUT to boot.

    Raises AbortRunException if the DUT does not come up — there is no point
    continuing the run if the board is not powered.
    """
    def _execute(self, config: TestConfig, assets, run_data: dict) -> TestResult.TestEval:
        TestLogger().info("DUT setup: configuring PSU (3.3 V, 0.5 A limit)")
        assets.psu.set_voltage(3.3)
        assets.psu.set_current_limit(0.5)

        TestLogger().debug("DUT setup: enabling PSU output")
        assets.psu.enable()          # relay closes; 50 ms settle simulated

        # Quick sanity: measure the main rail right after power-on
        rail_v = assets.psu.measure_voltage("main")
        TestLogger().debug(f"DUT setup: main rail after enable = {rail_v:.3f} V")
        if rail_v < 3.0:
            raise AbortRunException(
                f"DUT did not power up: main rail reads {rail_v:.3f} V"
            )

        TestLogger().info("DUT setup complete")
        return TestResult.TestEval.PASS


class DutCleanup(PassFailTestCase):
    """Disable the PSU at the end of the run."""
    def _execute(self, config: TestConfig, assets, run_data: dict) -> TestResult.TestEval:
        TestLogger().info("DUT cleanup: disabling PSU output")
        assets.psu.disable()
        return TestResult.TestEval.PASS


class SuiteSetup(PassFailTestCase):
    """Verify the DUT is still responsive before each test suite."""
    def _execute(self, config: TestConfig, assets, run_data: dict) -> TestResult.TestEval:
        rail_v = assets.psu.measure_voltage("main")
        TestLogger().debug(f"Suite setup: main rail = {rail_v:.3f} V")
        if rail_v < 3.0:
            raise AbortRunException(
                f"DUT unresponsive at suite start: rail reads {rail_v:.3f} V"
            )
        return TestResult.TestEval.PASS


class SuiteCleanup(PassFailTestCase):
    """No-op suite teardown (placeholder for real hardware drain / reset)."""
    def _execute(self, config: TestConfig, assets, run_data: dict) -> TestResult.TestEval:
        TestLogger().debug("Suite cleanup: done")
        return TestResult.TestEval.PASS

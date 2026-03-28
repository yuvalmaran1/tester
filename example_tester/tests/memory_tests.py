"""
memory_tests.py
===============
Non-volatile memory and RAM integrity tests.

Flash write-verify writes a known pattern and reads it back (simulated ~200 ms).
EEPROM write-verify tests the configuration storage area.
RAM test runs a walking-ones pattern across all addressable RAM.
All three use PassFailTestCase — the result is binary; there is no useful
numeric value to capture.
"""
from tester.TestConfig import TestConfig
from tester.TestResult import TestResult
from tester.TestResults.PassFailTestResult import PassFailTestCase
from tester.TestLogger import TestLogger


class FlashWriteVerifyTest(PassFailTestCase):
    """Write a pattern to flash and verify the read-back matches.

    Simulates ~200 ms (the typical flash erase+write cycle time).
    Failure rate: ~1 % (random.random() > 0.01).
    """
    def _execute(self, config: TestConfig, assets, run_data: dict) -> TestResult.TestEval:
        TestLogger().debug("Starting flash write/verify (erase + write + read-back)")
        ok = assets.dut.flash_write_verify()
        if ok:
            TestLogger().info("Flash write/verify passed")
        else:
            TestLogger().error("Flash write/verify FAILED — read-back mismatch")
        return TestResult.TestEval.PASS if ok else TestResult.TestEval.FAIL


class EEPROMWriteVerifyTest(PassFailTestCase):
    """Write and verify the DUT's EEPROM (configuration / calibration storage).

    Failure rate: ~1 %.
    """
    def _execute(self, config: TestConfig, assets, run_data: dict) -> TestResult.TestEval:
        TestLogger().debug("Starting EEPROM write/verify")
        ok = assets.dut.eeprom_write_verify()
        if ok:
            TestLogger().info("EEPROM write/verify passed")
        else:
            TestLogger().error("EEPROM write/verify FAILED")
        return TestResult.TestEval.PASS if ok else TestResult.TestEval.FAIL


class RAMTest(PassFailTestCase):
    """Run a walking-ones pattern across all addressable RAM.

    Failure rate: ~0.5 % — lower than flash because RAM errors are less common.
    """
    def _execute(self, config: TestConfig, assets, run_data: dict) -> TestResult.TestEval:
        TestLogger().debug("Starting RAM walking-ones test")
        ok = assets.dut.ram_test()
        if ok:
            TestLogger().info("RAM test passed")
        else:
            TestLogger().error("RAM test FAILED — memory fault detected")
        return TestResult.TestEval.PASS if ok else TestResult.TestEval.FAIL

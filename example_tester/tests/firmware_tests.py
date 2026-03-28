"""
firmware_tests.py
=================
Firmware identity and integrity checks.

These tests confirm the expected firmware and bootloader versions are running
and that the flash image has a valid CRC — the minimum bar before any
functional testing begins.
"""
from tester.TestConfig import TestConfig
from tester.TestResult import TestResult
from tester.TestResults.StringTestResult import StringTestCase
from tester.TestResults.PassFailTestResult import PassFailTestCase
from tester.TestUtil import AbortRunException
from tester.TestLogger import TestLogger


class FirmwareVersionTest(StringTestCase):
    """Read the firmware version string from the DUT.

    Tolerance in duts.json: {"expected": "2.1.4"}
    Fails if the DUT reports a different version, preventing mismatched firmware
    from passing production test.
    """
    def _execute(self, config: TestConfig, assets, run_data: dict) -> str:
        TestLogger().debug("Reading firmware version from DUT")
        version = assets.dut.get_firmware_version()
        TestLogger().info(f"DUT firmware version: {version}")
        return version


class BootloaderVersionTest(StringTestCase):
    """Read the bootloader version string from the DUT.

    Tolerance in duts.json: {"expected": "1.0.3"}
    """
    def _execute(self, config: TestConfig, assets, run_data: dict) -> str:
        TestLogger().debug("Reading bootloader version from DUT")
        version = assets.dut.get_bootloader_version()
        TestLogger().info(f"DUT bootloader version: {version}")
        return version


class FlashIntegrityTest(PassFailTestCase):
    """Verify the flash image CRC reported by the DUT bootloader.

    The simulator models a realistic 2 % CRC failure rate (random.random() > 0.02).
    On a real board this catches corrupted firmware images or failed flash writes.
    Raises AbortRunException on failure — remaining tests are meaningless if the
    firmware image is corrupt.
    """
    def _execute(self, config: TestConfig, assets, run_data: dict) -> TestResult.TestEval:
        TestLogger().debug("Requesting flash CRC check from DUT")
        if not assets.dut.flash_crc_ok():
            TestLogger().error("Flash CRC check failed — firmware image may be corrupt")
            raise AbortRunException("Flash CRC check failed — firmware image corrupt")
        TestLogger().info("Flash CRC OK")
        return TestResult.TestEval.PASS

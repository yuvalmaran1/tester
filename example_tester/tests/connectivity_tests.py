"""
connectivity_tests.py
=====================
UART, WiFi, and Bluetooth LE connectivity checks.

UARTLoopbackTest
    Sends a byte pattern over the DUT's debug UART and checks the echo.
    Simulates 100 ms latency.  Always passes in the simulator.

WiFiRSSITest (NumericTestCase)
    Reads the RSSI of the station's test AP from the DUT.  Returns a negative
    dBm value; the tolerance specifies the minimum acceptable signal level
    (e.g. min = −75 dBm).  In the simulator the reading is Gaussian around
    −52 dBm with 6 dBm σ.

BLEAdvertisingTest
    Checks that the DUT is broadcasting BLE advertisements.  In production this
    would scan for the DUT's MAC address; here the DUT always advertises.
"""
from tester.TestConfig import TestConfig
from tester.TestResult import TestResult
from tester.TestResults.PassFailTestResult import PassFailTestCase
from tester.TestResults.NumericTestResult import NumericTestCase
from tester.TestLogger import TestLogger


class UARTLoopbackTest(PassFailTestCase):
    """Send a test pattern over UART and verify the echo (100 ms round-trip)."""
    def _execute(self, config: TestConfig, assets, run_data: dict) -> TestResult.TestEval:
        TestLogger().debug("Sending UART loopback pattern")
        ok = assets.dut.uart_loopback_ok()
        if ok:
            TestLogger().info("UART loopback OK")
        else:
            TestLogger().error("UART loopback FAILED — no echo received")
        return TestResult.TestEval.PASS if ok else TestResult.TestEval.FAIL


class WiFiRSSITest(NumericTestCase):
    """Measure the DUT's WiFi RSSI to the station AP (dBm).

    Tolerance in duts.json: {"min": -75.0, "max": 0.0}
    A value below −75 dBm indicates poor RF performance or antenna fault.
    The simulator returns Gaussian(−52, 6) dBm.
    """
    def _execute(self, config: TestConfig, assets, run_data: dict) -> float:
        TestLogger().debug("Reading Wi-Fi RSSI from DUT")
        rssi = assets.dut.get_wifi_rssi_dbm()
        TestLogger().info(f"Wi-Fi RSSI = {rssi:.1f} dBm")
        return rssi


class BLEAdvertisingTest(PassFailTestCase):
    """Verify the DUT is broadcasting BLE advertisements.

    In production this would use a BLE sniffer or dongle to scan for the
    DUT's MAC address within a timeout window.
    """
    def _execute(self, config: TestConfig, assets, run_data: dict) -> TestResult.TestEval:
        TestLogger().debug("Checking BLE advertising state")
        ok = assets.dut.ble_advertising()
        if ok:
            TestLogger().info("BLE advertising confirmed")
        else:
            TestLogger().error("BLE advertising NOT detected")
        return TestResult.TestEval.PASS if ok else TestResult.TestEval.FAIL

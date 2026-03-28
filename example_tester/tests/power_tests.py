"""
power_tests.py
==============
Power-rail and current-consumption measurements.

Each test reads its target rail / operating-state from config.attr so that the
same test class can be reused for every rail in duts.json without duplication.
The PSU simulator adds Gaussian noise, so results vary realistically between runs.
"""
from tester.TestConfig import TestConfig
from tester.TestResults.NumericTestResult import NumericTestCase
from tester.TestLogger import TestLogger


class VoltageRailTest(NumericTestCase):
    """Measure a named supply rail voltage (V).

    Expected config.attr keys:
        rail (str): one of "3v3", "1v8", "5v", "main"

    The PSU simulator returns nominal ± 0.4 % (1σ), matching a real bench supply.
    """
    def _execute(self, config: TestConfig, assets, run_data: dict) -> float:
        rail = config.attr.get("rail", "main")
        TestLogger().debug(f"Measuring PSU voltage on rail '{rail}'")
        voltage = assets.psu.measure_voltage(rail)
        TestLogger().debug(f"Rail '{rail}' = {voltage:.4f} V")
        return voltage


class CurrentDrawTest(NumericTestCase):
    """Measure DUT supply current (mA) at a given operating state.

    Expected config.attr keys:
        state (str): "idle" (~48 mA nominal) or "active" (~125 mA nominal)

    The simulator adds 4 % Gaussian noise to model real switching noise.
    """
    def _execute(self, config: TestConfig, assets, run_data: dict) -> float:
        state = config.attr.get("state", "idle")
        TestLogger().debug(f"Measuring current draw in state '{state}'")
        current = assets.psu.measure_current_ma(state)
        TestLogger().debug(f"Current ({state}) = {current:.2f} mA")
        return current


class IndependentVoltageTest(NumericTestCase):
    """Verify a rail voltage using the DMM (higher accuracy than the PSU readback).

    Uses the DMM's 0.1 % sigma vs the PSU's 0.4 % sigma, catching PSU
    calibration drift.  Expected config.attr key: rail (str).
    """
    def _execute(self, config: TestConfig, assets, run_data: dict) -> float:
        rail = config.attr.get("rail", "3v3")
        TestLogger().debug(f"Measuring DMM voltage on rail '{rail}'")
        voltage = assets.dmm.measure_dc_voltage(rail)
        TestLogger().debug(f"DMM rail '{rail}' = {voltage:.4f} V")
        return voltage

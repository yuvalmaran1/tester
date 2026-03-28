"""
example_tester_code_duts.py
===========================
Shows how to define DUTs entirely in Python instead of a duts.json file.

Two approaches are demonstrated:

  A. Dict-based  — build the same structure that duts.json would contain as a
                   plain Python dict, then delegate to the default populate_duts().
                   Good for simple cases or when you want to keep the familiar
                   schema but generate it from code (e.g. from a database).

  B. Object-based — construct Dut / TestSuite / TestProgram / TestCase objects
                    directly and override populate_duts() to return them.
                    Good when DUT definitions need real Python logic (loops,
                    conditionals, factory functions, etc.).
"""
import copy
from dataclasses import dataclass

from tester import Tester
from tester.TesterConfig import TesterConfig
from tester.StationConfig import StationConfig

# Framework classes needed for approach B
from tester.Dut import Dut
from tester.TestSuite import TestSuite
from tester.TestProgram import TestProgram
from tester.TestConfig import TestConfig
from tester.TestResult import TestResult
from tester.TestResults.NumericTestResult import NumericTestCase
from tester.TestResults.PassFailTestResult import PassFailTestCase
from tester.TestResults.StringTestResult import StringTestCase


# ── Station config & assets ───────────────────────────────────────────────────

class MyStationConfig(StationConfig):
    serial_port: str = "COM1"
    ip_address: str  = "127.0.0.1"


@dataclass
class MyAssets:
    # Add instrument handles here; e.g.:
    # instrument: MyInstrument
    pass


# ── Test case definitions ─────────────────────────────────────────────────────

class PowerOnSetup(PassFailTestCase):
    def _execute(self, config, assets: MyAssets, run_data) -> TestResult.TestEval:
        return TestResult.TestEval.PASS

class PowerOffCleanup(PassFailTestCase):
    def _execute(self, config, assets: MyAssets, run_data) -> TestResult.TestEval:
        return TestResult.TestEval.PASS

class VoltageTest(NumericTestCase):
    def _execute(self, config, assets: MyAssets, run_data) -> float:
        rail = config.attr.get("rail", "3v3")
        # return assets.instrument.measure_voltage(rail)
        return 3.31

class FirmwareVersionTest(StringTestCase):
    def _execute(self, config, assets: MyAssets, run_data) -> str:
        # return assets.instrument.get_firmware_version()
        return "1.2.3"


# ═════════════════════════════════════════════════════════════════════════════
# APPROACH A — dict-based
# ─────────────────────────────────────────────────────────────────────────────
# Build the exact same structure that duts.json would contain and pass it to
# populate_duts().  The framework's from_dict() parsers do the rest.
# ═════════════════════════════════════════════════════════════════════════════

# Module path must be importable; here it's the current module itself.
_THIS_MODULE = "example_tester_code_duts"

DUTS_DICT = {
    "duts": [
        {
            "name": "Board Rev A",
            "description": "Main controller PCB, hardware revision A",
            "product_id": "PCB-001-A",
            "image": "",
            "module": _THIS_MODULE,
            "setup":   "PowerOnSetup",
            "cleanup": "PowerOffCleanup",
            "attr": {"hw_rev": "A"},
            "testsuites": [
                {
                    "name": "Power Rails",
                    "module": _THIS_MODULE,
                    "setup":   "PowerOnSetup",
                    "cleanup": "PowerOffCleanup",
                    "attr": {"supply_voltage": 3.3},
                    "testcases": [
                        {
                            "name": "3.3V Rail",
                            "test": "VoltageTest",
                            "tolerance": {"min": 3.2, "max": 3.4},
                            "unit": "V",
                            "attr": {"rail": "3v3"},
                        },
                        {
                            "name": "5V Rail",
                            "test": "VoltageTest",
                            "tolerance": {"min": 4.9, "max": 5.1},
                            "unit": "V",
                            "attr": {"rail": "5v"},
                        },
                    ],
                },
                {
                    "name": "Firmware",
                    "module": _THIS_MODULE,
                    "testcases": [
                        {
                            "name": "FW Version",
                            "test": "FirmwareVersionTest",
                            "tolerance": {"expected": "1.2.3"},
                        },
                    ],
                },
            ],
            "programs": [
                {
                    "name": "Quick Sanity",
                    "description": "Fast pre-production check",
                    "testsuites": ["Power Rails"],
                },
                {
                    "name": "Full Production",
                    "description": "Complete production test sequence",
                    "testsuites": ["Power Rails", "Firmware"],
                },
            ],
        }
    ]
}


class TesterWithDictDuts(Tester):
    """Approach A: feed a Python dict to the default populate_duts()."""

    def __init__(self, ui=True):
        cfg = TesterConfig(
            name="Dict-DUT Tester",
            version="1.0.0",
            db_config="./results_dict.db",
            station_config_file="./station.json",
            duts_file="./duts.json",
            station_config_class=MyStationConfig,
            ui=ui,
        )
        super().__init__(cfg)

    def _init(self, station_config: MyStationConfig) -> MyAssets:
        return MyAssets()

    def populate_duts(self, _ignored_json):
        # Ignore the file that was loaded; use the in-code dict instead.
        return super().populate_duts(DUTS_DICT)


# ═════════════════════════════════════════════════════════════════════════════
# APPROACH B — object-based
# ─────────────────────────────────────────────────────────────────────────────
# Construct Dut / TestSuite / TestProgram / TestCase objects directly.
# Useful when DUT structure is generated by logic (loops, external data, etc.)
# ═════════════════════════════════════════════════════════════════════════════

def _make_config(name, *, tolerance=None, unit="", attr=None, infoonly=False):
    """Convenience wrapper around TestConfig."""
    cfg = TestConfig(attr=attr or {}, tolerance=tolerance or {})
    cfg.name = name
    cfg.unit = unit
    cfg.infoonly = infoonly
    return cfg


def _build_power_suite(assets, dut_attr: dict) -> TestSuite:
    suite_attr = {"supply_voltage": 3.3} | dut_attr

    ts = TestSuite()
    ts.name = "Power Rails"
    ts.attr = suite_attr

    setup_cfg = TestConfig(attr=suite_attr, tolerance={})
    setup_cfg.name = "Setup"
    ts.setup = PowerOnSetup(setup_cfg, assets, ts.name)

    cleanup_cfg = TestConfig(attr=suite_attr, tolerance={})
    cleanup_cfg.name = "Cleanup"
    ts.cleanup = PowerOffCleanup(cleanup_cfg, assets, ts.name)

    # Generate test cases from a table — easy to extend without editing JSON
    rails = [
        ("3.3V Rail", "3v3", 3.2, 3.4),
        ("5V Rail",   "5v",  4.9, 5.1),
    ]
    for name, rail_id, lo, hi in rails:
        cfg = _make_config(
            name,
            tolerance={"min": lo, "max": hi},
            unit="V",
            attr=suite_attr | {"rail": rail_id},
        )
        ts.testcases.append(VoltageTest(cfg, assets, ts.name))

    return ts


def _build_firmware_suite(assets, dut_attr: dict) -> TestSuite:
    ts = TestSuite()
    ts.name = "Firmware"
    ts.attr = dut_attr

    cfg = _make_config("FW Version", tolerance={"expected": "1.2.3"}, attr=dut_attr)
    ts.testcases.append(FirmwareVersionTest(cfg, assets, ts.name))

    return ts


def _build_dut(assets) -> Dut:
    dut = Dut()
    dut.name = "Board Rev A"
    dut.description = "Main controller PCB, hardware revision A"
    dut.product_id = "PCB-001-A"
    dut.attr = {"hw_rev": "A"}
    dut.assets = assets

    # DUT-level setup / cleanup
    setup_cfg = TestConfig(attr=dut.attr, tolerance={})
    setup_cfg.name = "Setup"
    dut.setup = PowerOnSetup(setup_cfg, assets, "")

    cleanup_cfg = TestConfig(attr=dut.attr, tolerance={})
    cleanup_cfg.name = "Cleanup"
    dut.cleanup = PowerOffCleanup(cleanup_cfg, assets, "")

    # Build suites
    power_suite    = _build_power_suite(assets, dut.attr)
    firmware_suite = _build_firmware_suite(assets, dut.attr)
    dut.test_suites = [power_suite, firmware_suite]

    # Programs reference suites by deep-copying them (same as TestProgram.from_dict)
    quick = TestProgram()
    quick.name = "Quick Sanity"
    quick.description = "Fast pre-production check"
    quick.testsuites = [copy.deepcopy(power_suite)]

    full = TestProgram()
    full.name = "Full Production"
    full.description = "Complete production test sequence"
    full.testsuites = [copy.deepcopy(power_suite), copy.deepcopy(firmware_suite)]

    dut.programs = [quick, full]
    return dut


class TesterWithObjectDuts(Tester):
    """Approach B: build Dut objects directly, bypassing JSON entirely."""

    def __init__(self, ui=True):
        cfg = TesterConfig(
            name="Object-DUT Tester",
            version="1.0.0",
            db_config="./results_obj.db",
            station_config_file="./station.json",
            duts_file="./duts.json",
            station_config_class=MyStationConfig,
            ui=ui,
        )
        super().__init__(cfg)

    def _init(self, station_config: MyStationConfig) -> MyAssets:
        return MyAssets()

    def populate_duts(self, _ignored_json):
        # Build and return the DUT list directly; JSON file is ignored.
        return [_build_dut(self.assets)]


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Switch between approach A and B by changing the class here.
    TesterWithObjectDuts()

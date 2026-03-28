"""
example_tester.py
=================
Smart Sensor Board — Production Tester

A realistic reference implementation of the tester framework for a hypothetical
IoT "Smart Sensor Board" (Wi-Fi + BLE, temperature/humidity sensors, 3.3 V / 1.8 V
/ 5 V supply rails).

To adapt this for real hardware:
  1. Replace SimulatedPSU / SimulatedDMM / SimulatedDUT / SimulatedReferenceSensor
     with real instrument drivers (GPIB, USB-TMC, UART, etc.).
  2. Update SensorBoardStationConfig with the fields your hardware needs.
  3. Adjust tolerances in duts.json to match your DUT spec.

Run from the example_tester directory:
    python example_tester.py
"""
from dataclasses import dataclass

from tester import Tester
from tester.TesterConfig import TesterConfig
from tester.StationConfig import StationConfig

from instruments.simulated_instruments import (
    SimulatedPSU,
    SimulatedDMM,
    SimulatedDUT,
    SimulatedReferenceSensor,
)


# ── Station configuration ──────────────────────────────────────────────────────
# Each test station supplies its own station.json with these values.
# The defaults below match the bundled station.json for a simulator run.

class SensorBoardStationConfig(StationConfig):
    """Per-station hardware addresses and calibration constants.

    In a multi-station factory each station has a different station.json;
    the Python code never changes between stations.
    """
    psu_address: str    = "192.168.1.10"   # SCPI-over-LAN address of the PSU
    dmm_address: str    = "192.168.1.11"   # SCPI-over-LAN address of the DMM
    dut_port: str       = "COM3"           # Serial port of the DUT test jig
    reference_temp: float = 25.0           # Ambient reference temperature (°C)


# ── Assets dataclass ───────────────────────────────────────────────────────────
# One field per instrument.  Type annotations allow IDEs to auto-complete
# inside every _execute(self, config, assets: SensorBoardAssets, run_data).

@dataclass
class SensorBoardAssets:
    psu:       SimulatedPSU
    dmm:       SimulatedDMM
    dut:       SimulatedDUT
    reference: SimulatedReferenceSensor


# ── Tester subclass ────────────────────────────────────────────────────────────

class SensorBoardTester(Tester):
    def __init__(self, ui: bool = True) -> None:
        cfg = TesterConfig(
            name="Smart Sensor Board Production Tester",
            description="Production test system for the Smart Sensor Board (Wi-Fi + BLE, temp/humidity)",
            version="1.0.0",
            db_config="./TestDB.db",
            duts_file="./duts.json",
            log_dir=None,
            ui=ui,
            station_config_file="./station.json",
            station_config_class=SensorBoardStationConfig,
        )
        super().__init__(cfg)

    def _init(self, station_config: SensorBoardStationConfig) -> SensorBoardAssets:
        """Open all instrument connections and return typed assets.

        Replace each Simulated* class with a real driver to move from
        simulation to production.
        """
        return SensorBoardAssets(
            psu       = SimulatedPSU(ip=station_config.psu_address),
            dmm       = SimulatedDMM(),
            dut       = SimulatedDUT(port=station_config.dut_port),
            reference = SimulatedReferenceSensor(
                            reference_temp=station_config.reference_temp
                        ),
        )


if __name__ == "__main__":
    SensorBoardTester()

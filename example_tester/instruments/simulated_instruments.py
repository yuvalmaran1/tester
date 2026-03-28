"""
simulated_instruments.py
========================
Lightweight instrument simulators that stand in for real hardware.

Each class models a real bench instrument — a programmable power supply,
a digital multimeter, the DUT's own debug/serial interface, and a calibrated
reference sensor — returning physically plausible values with additive
Gaussian noise so that runs produce varied but realistic results.

In a real tester you would replace these classes with drivers that talk to
actual hardware over GPIB, USB-TMC, UART, etc.
"""
import logging
import random
import time

logger = logging.getLogger(__name__)


class SimulatedPSU:
    """Programmable bench power supply (e.g. Keysight E36312A).

    Controls the DUT supply rail and measures output voltage / current.
    """

    def __init__(self, ip: str):
        self.ip = ip
        self._enabled = False
        self._set_voltage = 5.0          # V
        self._set_current_limit = 1.0    # A
        logger.debug(f"SimulatedPSU: connected to {ip}")

    # ── Output control ──────────────────────────────────────────────────────

    def set_voltage(self, volts: float):
        logger.debug(f"PSU: set voltage → {volts} V")
        self._set_voltage = volts

    def set_current_limit(self, amps: float):
        logger.debug(f"PSU: set current limit → {amps} A")
        self._set_current_limit = amps

    def enable(self):
        logger.debug("PSU: enabling output (relay close + 50 ms settle)")
        self._enabled = True
        time.sleep(0.05)   # simulate relay close / inrush settling

    def disable(self):
        logger.debug("PSU: disabling output")
        self._enabled = False

    # ── Measurements ────────────────────────────────────────────────────────

    def measure_voltage(self, rail: str = "main") -> float:
        """Return the measured output voltage (V) of the named rail."""
        nominals = {
            "3v3":  3.300,
            "1v8":  1.800,
            "5v":   5.000,
            "main": self._set_voltage,
        }
        nominal = nominals.get(rail, self._set_voltage)
        value = random.gauss(nominal, nominal * 0.004)   # 0.4 % sigma
        logger.debug(f"PSU: measure_voltage('{rail}') → {value:.4f} V")
        return value

    def measure_current_ma(self, state: str = "idle") -> float:
        """Return the DUT supply current (mA) at the given operating state."""
        nominals = {"idle": 48.0, "active": 125.0}
        nominal = nominals.get(state, 48.0)
        value = random.gauss(nominal, nominal * 0.04)    # 4 % sigma
        logger.debug(f"PSU: measure_current_ma('{state}') → {value:.2f} mA")
        return value


class SimulatedDMM:
    """Benchtop digital multimeter (e.g. Keysight 34465A).

    Used for independent rail verification with tighter accuracy than the PSU.
    """

    def measure_dc_voltage(self, channel: str) -> float:
        nominals = {"3v3": 3.300, "1v8": 1.800, "5v": 5.000}
        nominal = nominals.get(channel, 3.3)
        value = random.gauss(nominal, nominal * 0.001)   # 0.1 % sigma
        logger.debug(f"DMM: measure_dc_voltage('{channel}') → {value:.4f} V")
        return value


class SimulatedDUT:
    """The DUT's firmware debug / production-test interface.

    In production this communicates over a serial/USB port, JTAG, or a
    proprietary protocol.  Here every command is simulated in software.
    """

    # Nominal sensor characteristics — slight unit-to-unit variation
    _TEMP_OFFSET  = random.gauss(0.0, 0.3)    # °C   per-unit sensor offset
    _HUMID_OFFSET = random.gauss(0.0, 1.0)    # %RH  per-unit sensor offset

    def __init__(self, port: str):
        self.port = port
        self._serial_number: str = ""
        self._cal_offset: float = 0.0
        logger.debug(f"SimulatedDUT: connected on port {port}")

    # ── Identity / firmware ─────────────────────────────────────────────────

    def get_firmware_version(self) -> str:
        version = "2.1.4"
        logger.debug(f"DUT: get_firmware_version() → {version}")
        return version

    def get_bootloader_version(self) -> str:
        version = "1.0.3"
        logger.debug(f"DUT: get_bootloader_version() → {version}")
        return version

    def flash_crc_ok(self) -> bool:
        result = random.random() > 0.02   # realistic 2 % failure rate
        logger.debug(f"DUT: flash_crc_ok() → {result}")
        return result

    # ── Memory ─────────────────────────────────────────────────────────────

    def flash_write_verify(self) -> bool:
        logger.debug("DUT: flash_write_verify() — erasing + writing + verifying (~200 ms)")
        time.sleep(0.2)
        result = random.random() > 0.01
        logger.debug(f"DUT: flash_write_verify() → {result}")
        return result

    def eeprom_write_verify(self) -> bool:
        logger.debug("DUT: eeprom_write_verify()")
        result = random.random() > 0.01
        logger.debug(f"DUT: eeprom_write_verify() → {result}")
        return result

    def ram_test(self) -> bool:
        logger.debug("DUT: ram_test() — walking-ones pattern")
        result = random.random() > 0.005
        logger.debug(f"DUT: ram_test() → {result}")
        return result

    # ── Sensors ─────────────────────────────────────────────────────────────

    def get_temperature_c(self) -> float:
        """Raw reading from the DUT's on-chip temperature sensor."""
        value = random.gauss(25.0 + self._TEMP_OFFSET, 0.5)
        logger.debug(f"DUT: get_temperature_c() → {value:.3f} °C")
        return value

    def get_humidity_pct(self) -> float:
        """Raw reading from the DUT's humidity sensor."""
        value = random.gauss(45.0 + self._HUMID_OFFSET, 1.2)
        logger.debug(f"DUT: get_humidity_pct() → {value:.2f} %RH")
        return value

    # ── Connectivity ────────────────────────────────────────────────────────

    def uart_loopback_ok(self) -> bool:
        logger.debug("DUT: uart_loopback_ok() — sending pattern, waiting for echo (~100 ms)")
        time.sleep(0.1)
        logger.debug("DUT: uart_loopback_ok() → True")
        return True

    def get_wifi_rssi_dbm(self) -> float:
        """WiFi receive signal strength from station AP."""
        value = random.gauss(-52.0, 6.0)    # dBm
        logger.debug(f"DUT: get_wifi_rssi_dbm() → {value:.1f} dBm")
        return value

    def ble_advertising(self) -> bool:
        logger.debug("DUT: ble_advertising() → True")
        return True

    # ── Calibration & programming ───────────────────────────────────────────

    def write_temp_cal_offset(self, offset_c: float) -> bool:
        """Write the calibration offset to the DUT's NV storage."""
        logger.debug(f"DUT: write_temp_cal_offset({offset_c:+.3f} °C)")
        self._cal_offset = offset_c
        return True

    def write_serial_number(self, sn: str) -> bool:
        logger.debug(f"DUT: write_serial_number('{sn}')")
        self._serial_number = sn
        return True

    def read_serial_number(self) -> str:
        logger.debug(f"DUT: read_serial_number() → '{self._serial_number}'")
        return self._serial_number


class SimulatedReferenceSensor:
    """High-accuracy calibrated reference sensor at the test fixture.

    Used as a traceable reference for DUT sensor calibration.
    Accuracy is an order of magnitude better than the DUT sensor.
    """

    def __init__(self, reference_temp: float = 25.0):
        self._ref_temp = reference_temp
        logger.debug(f"SimulatedReferenceSensor: reference_temp = {reference_temp} °C")

    def get_temperature_c(self) -> float:
        value = random.gauss(self._ref_temp, 0.05)   # ±0.05 °C 1-sigma
        logger.debug(f"Reference: get_temperature_c() → {value:.4f} °C")
        return value

    def get_humidity_pct(self) -> float:
        value = random.gauss(45.0, 0.2)              # ±0.2 %RH 1-sigma
        logger.debug(f"Reference: get_humidity_pct() → {value:.3f} %RH")
        return value

"""
sensor_tests.py
===============
Environmental sensor accuracy and calibration tests.

TemperatureErrorTest / HumidityErrorTest
    Measure the raw DUT sensor reading against the traceable reference sensor
    and return the absolute error.  Tolerance in duts.json specifies the maximum
    acceptable raw error before calibration (e.g. ±2 °C).

TemperatureSweepTest (Numeric2dTestCase)
    Takes N repeated samples and builds a scatter plot of (sample index, DUT−Ref
    error).  The plot appears in the UI and is saved with the run.  Tolerance is
    a per-point band (e.g. ±3 °C) that every sample must satisfy.

All three use run_data to pass the reference temperature to the calibration suite
so that ComputeCalibrationTest can calculate the correction offset without
re-reading the reference sensor.
"""
import numpy as np
from tester.TestConfig import TestConfig
from tester.TestResults.NumericTestResult import NumericTestCase
from tester.TestResults.Numeric2dTestResult import Numeric2dTestCase
from tester.TestLogger import TestLogger


class TemperatureErrorTest(NumericTestCase):
    """Return DUT temperature error relative to the reference sensor (°C).

    Positive values mean the DUT reads high; negative means it reads low.
    Stores the reference reading in run_data so calibration can use it later.
    """
    def _execute(self, config: TestConfig, assets, run_data: dict) -> float:
        TestLogger().debug("Reading reference and DUT temperatures")
        ref_temp  = assets.reference.get_temperature_c()
        dut_temp  = assets.dut.get_temperature_c()
        error     = dut_temp - ref_temp

        TestLogger().info(
            f"Temperature: Ref={ref_temp:.3f} °C  DUT={dut_temp:.3f} °C  "
            f"Error={error:+.3f} °C"
        )

        # Share with calibration suite (see programming_tests.ComputeCalibrationTest)
        run_data["ref_temp"] = ref_temp
        run_data["dut_temp"] = dut_temp

        self.set_comment(
            f"DUT={dut_temp:.2f} °C  Ref={ref_temp:.2f} °C  Error={error:+.2f} °C"
        )
        return error


class HumidityErrorTest(NumericTestCase):
    """Return DUT humidity error relative to the reference sensor (%RH).

    Tolerance in duts.json: {"min": -3.0, "max": 3.0}
    """
    def _execute(self, config: TestConfig, assets, run_data: dict) -> float:
        TestLogger().debug("Reading reference and DUT humidity")
        ref_rh = assets.reference.get_humidity_pct()
        dut_rh = assets.dut.get_humidity_pct()
        error  = dut_rh - ref_rh

        TestLogger().info(
            f"Humidity: Ref={ref_rh:.2f} %RH  DUT={dut_rh:.2f} %RH  "
            f"Error={error:+.2f} %RH"
        )

        self.set_comment(
            f"DUT={dut_rh:.1f} %RH  Ref={ref_rh:.1f} %RH  Error={error:+.1f} %RH"
        )
        return error


class TemperatureSweepTest(Numeric2dTestCase):
    """Capture N temperature samples and plot the DUT−Reference error over time.

    x-axis: sample index (1 … N)
    y-axis: DUT temperature error (°C)
    Tolerance: per-point band, e.g. {"min": -3.0, "max": 3.0}

    Demonstrates the Numeric2dTestCase type: the UI renders the data as a line
    chart and every point is checked against the band tolerance.

    config.attr keys:
        n_samples (int): number of samples to take (default 20)
    """
    def _execute(self, config: TestConfig, assets, run_data: dict) -> dict:
        n = int(config.attr.get("n_samples", 20))
        TestLogger().info(f"Temperature sweep: collecting {n} samples")

        x_values = list(range(1, n + 1))
        y_values = []

        for i in range(n):
            ref = assets.reference.get_temperature_c()
            dut = assets.dut.get_temperature_c()
            err = round(dut - ref, 4)
            y_values.append(err)
            TestLogger().debug(f"  Sample {i+1}/{n}: Ref={ref:.3f} °C  DUT={dut:.3f} °C  Error={err:+.4f} °C")

        mean_err = sum(y_values) / len(y_values)
        TestLogger().info(f"Temperature sweep complete. Mean error: {mean_err:+.3f} °C")
        self.set_comment(f"Mean error over {n} samples: {mean_err:+.3f} °C")

        return {"x": x_values, "y": y_values}

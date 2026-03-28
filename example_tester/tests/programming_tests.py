"""
programming_tests.py
====================
Calibration write and unit serialisation tests.

This module demonstrates two advanced framework features:

1. **run_data** — data flows between test cases within the same run without
   persisting across runs.  ComputeCalibrationTest writes the offset into
   run_data; WriteCalibrationTest reads it back and programs the DUT.
   VerifySerialNumberTest reads back the serial number that AssignSerialNumberTest
   stored in run_data, proving the NV write succeeded.

2. **TestDialog** — AssignSerialNumberTest suspends the run and prompts the
   operator to enter a serial number via the UI.  The run continues only after
   the operator clicks OK (or the 60-second timeout fires).
"""
from tester.TestConfig import TestConfig
from tester.TestResult import TestResult
from tester.TestResults.PassFailTestResult import PassFailTestCase
from tester.TestResults.NumericTestResult import NumericTestCase
from tester.TestUtil import AbortRunException, TestDialog
from tester.TestLogger import TestLogger


class ComputeCalibrationTest(NumericTestCase):
    """Compute the temperature calibration offset and store it in run_data.

    Uses the reference temperature measured (and stored) by TemperatureErrorTest
    in the Sensors suite.  Falls back to a fresh sensor read if Sensors has not
    run (e.g. in the Calibration Only program).

    Returns the offset value (°C) so the framework records it in the database.
    Tolerance in duts.json: {"min": -5.0, "max": 5.0} — reject boards whose
    sensor is too far out to be corrected by a single-point offset.
    """
    def _execute(self, config: TestConfig, assets, run_data: dict) -> float:
        # Prefer values already measured in the Sensors suite
        if "ref_temp" in run_data and "dut_temp" in run_data:
            TestLogger().debug("Using ref/DUT temps from run_data (measured in Sensors suite)")
            ref_temp = run_data["ref_temp"]
            dut_temp = run_data["dut_temp"]
        else:
            TestLogger().debug("Sensors suite did not run — taking fresh temperature readings")
            ref_temp = assets.reference.get_temperature_c()
            dut_temp = assets.dut.get_temperature_c()

        offset = ref_temp - dut_temp        # correction to add to raw DUT reading
        run_data["cal_offset"] = offset     # hand off to WriteCalibrationTest

        TestLogger().info(
            f"Calibration: Ref={ref_temp:.3f} °C  DUT raw={dut_temp:.3f} °C  "
            f"Offset={offset:+.3f} °C"
        )
        self.set_comment(
            f"Ref={ref_temp:.2f} °C  DUT raw={dut_temp:.2f} °C  "
            f"Offset={offset:+.3f} °C"
        )
        return offset


class WriteCalibrationTest(PassFailTestCase):
    """Write the calibration offset (from run_data) to the DUT's NV storage.

    Reads run_data['cal_offset'] set by ComputeCalibrationTest.  Raises
    AbortRunException if the offset was never computed (suite order error).
    """
    def _execute(self, config: TestConfig, assets, run_data: dict) -> TestResult.TestEval:
        offset = run_data.get("cal_offset")
        if offset is None:
            raise AbortRunException(
                "cal_offset not in run_data — did ComputeCalibrationTest run first?"
            )

        TestLogger().debug(f"Writing calibration offset {offset:+.3f} °C to DUT NV storage")
        ok = assets.dut.write_temp_cal_offset(offset)
        if not ok:
            TestLogger().error("Failed to write calibration offset to DUT NV storage")
            return TestResult.TestEval.FAIL

        TestLogger().info(f"Calibration offset {offset:+.3f} °C written successfully")
        self.set_comment(f"Wrote offset {offset:+.3f} °C to DUT NV storage")
        return TestResult.TestEval.PASS


class AssignSerialNumberTest(PassFailTestCase):
    """Prompt the operator for a serial number and program it into the DUT.

    Suspends the run and shows a UI dialog with a text input field.  The
    operator has 60 seconds to enter the serial number and click OK.  On
    timeout or Cancel the run is aborted.

    The serial number is stored in run_data['serial_number'] so that the
    following VerifySerialNumberTest can confirm the write succeeded.
    """
    def _execute(self, config: TestConfig, assets, run_data: dict) -> TestResult.TestEval:
        dialog = TestDialog()
        response = dialog.display(
            title="Assign Serial Number",
            text="Scan or type the serial number for this unit, then click OK.",
            schema={
                "type": "object",
                "properties": {
                    "serial_number": {
                        "type": "string",
                        "description": "Unit serial number (e.g. SN-2026-00042)",
                    }
                },
                "required": ["serial_number"],
            },
            defaults={"serial_number": ""},
            timeout=60,
            responses=[TestDialog.Response.Ok, TestDialog.Response.Cancel],
        )

        # display() returns {"rsp": "Ok"} / {"rsp": "Cancel"} (dict from the frontend)
        if (response or {}).get("rsp") != TestDialog.Response.Ok.name:
            TestLogger().warning("Operator cancelled serial number entry — aborting run")
            raise AbortRunException("Operator cancelled serial number entry")

        sn = (dialog.response_data or {}).get("serial_number", "").strip()
        if not sn:
            raise AbortRunException("No serial number entered")

        TestLogger().debug(f"Writing serial number '{sn}' to DUT")
        ok = assets.dut.write_serial_number(sn)
        if not ok:
            TestLogger().error(f"Failed to write serial number '{sn}' to DUT")
            return TestResult.TestEval.FAIL

        run_data["serial_number"] = sn      # pass to VerifySerialNumberTest
        TestLogger().info(f"Serial number programmed: {sn}")
        self.set_comment(f"Programmed serial number: {sn}")
        return TestResult.TestEval.PASS


class VerifySerialNumberTest(PassFailTestCase):
    """Read back the serial number from the DUT and confirm it matches run_data.

    Demonstrates run_data cross-test communication: the serial number written by
    AssignSerialNumberTest is compared against the DUT's NV read-back here.
    """
    def _execute(self, config: TestConfig, assets, run_data: dict) -> TestResult.TestEval:
        expected_sn = run_data.get("serial_number", "")
        TestLogger().debug("Reading serial number back from DUT NV storage")
        read_sn = assets.dut.read_serial_number()

        TestLogger().info(f"Serial number read back: {read_sn!r}  (expected: {expected_sn!r})")
        self.set_comment(f"Expected: {expected_sn!r}  Read back: {read_sn!r}")

        if not expected_sn:
            # AssignSerialNumberTest did not run (e.g. partial program) — treat
            # as informational: just log the read-back value.
            return TestResult.TestEval.PASS

        if read_sn != expected_sn:
            TestLogger().error(f"Serial number mismatch: wrote {expected_sn!r}, read back {read_sn!r}")
            return TestResult.TestEval.FAIL

        return TestResult.TestEval.PASS

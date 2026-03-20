"""RunExecutorMixin — test execution logic extracted from Tester.

Contains all methods responsible for running a test program:
  - Test statistics tracking (_reset_stats, _test_done)
  - Per-testsuite execution (_execute_testsuite)
  - Run lifecycle (run, _run, wait_for_test_end)
  - Low-level thread helpers (_get_run_thread_id, _ctype_async_raise)
  - Run object construction (_create_run)
  - Skip-state tracking (_store_original_skip_states, _track_program_modifications)
"""

import ctypes
import threading
from threading import Thread

from .TestResult import TestResult
from .TestSuite import TestSuite
from .TestLogger import TestLogger
from .TestRun import TestRun
from .TesterIf import TesterRequest
from .TestUtil import AbortRunException, TestAttachment
from .TestCase import TestCase


class RunExecutorMixin:
    """Mixin providing test run execution for Tester.

    Expects the host class to supply the following attributes on self:
    db, active_test, abort_run, running, test_run, active_program,
    active_dut, dut_setup, dut_cleanup, logger, attachment, run_attr,
    state, original_skip_states, interface, test_stats.
    """

    def _reset_stats(self, total=0):
        self.test_stats = {
            "total": total,
            "done": 0,
            TestResult.TestEval.PASS.name: 0,
            TestResult.TestEval.FAIL.name: 0,
            TestResult.TestEval.ERROR.name: 0,
            TestResult.TestEval.SKIPPED.name: 0,
            TestResult.TestEval.INFOONLY.name: 0,
            TestResult.TestEval.ABORTED.name: 0
        }

    def _test_done(self, result):
        self.test_stats['done'] += 1
        self.test_stats[result.name] += 1

    def _execute_testsuite(self, ts: TestSuite, run_id, skip_suite: bool = False):
        skip_testcases = False
        self._update_status(f"Executing Test Suite '{ts.name}'")
        if ts.setup:
            self._update_status(f"Executing Test Case '{ts.setup.config.name}'")
            if skip_suite or ts.setup.config.skip:
                ts.setup.skip()
                # Add comment if skipped due to user modification
                if hasattr(self, 'original_skip_states'):
                    test_id = f"{ts.name}_setup"
                    original_skip = self.original_skip_states.get(test_id, False)
                    if not original_skip and ts.setup.config.skip:
                        if ts.setup.result.comment:
                            ts.setup.result.comment += " | Skipped by user"
                        else:
                            ts.setup.result.comment = "Skipped by user"
            else:
                ts.setup.execute()
                skip_testcases = ts.setup.result.result != TestResult.TestEval.PASS
            self.db.append_result(ts.setup.result, run_id)
            self._update_run()
            self._test_done(ts.setup.result.result)
            self.active_test += 1
            self.logger.info(f"Test '{ts.setup.config.name}' complete. Result: {ts.setup.result.result.name}")

        for tc in ts.testcases:
            if self.abort_run:
                skip_testcases = True
            if skip_testcases or skip_suite or tc.config.skip:
                self._update_status(f"Skipping Test Case '{tc.config.name}'")
                tc.skip()
                # Add comment if skipped due to user modification
                if hasattr(self, 'original_skip_states'):
                    test_id = f"{ts.name}_{tc.config.name}"
                    original_skip = self.original_skip_states.get(test_id, False)
                    if not original_skip and tc.config.skip:
                        if tc.result.comment:
                            tc.result.comment += " | Skipped by user"
                        else:
                            tc.result.comment = "Skipped by user"
            else:
                self._update_status(f"Executing Test Case '{tc.config.name}'")
                tc.execute()
            self.db.append_result(tc.result, run_id)
            self._update_run()
            self._test_done(tc.result.result)
            self.active_test += 1
            self.logger.info(f"Test '{tc.config.name}' complete. Result: {tc.result.result.name}")

        if ts.cleanup:
            self._update_status(f"Executing Test Case '{ts.cleanup.config.name}'")
            if skip_suite or ts.cleanup.config.skip:
                ts.cleanup.skip()
                # Add comment if skipped due to user modification
                if hasattr(self, 'original_skip_states'):
                    test_id = f"{ts.name}_cleanup"
                    original_skip = self.original_skip_states.get(test_id, False)
                    if not original_skip and ts.cleanup.config.skip:
                        if ts.cleanup.result.comment:
                            ts.cleanup.result.comment += " | Skipped by user"
                        else:
                            ts.cleanup.result.comment = "Skipped by user"
            else:
                ts.cleanup.execute()
            self.db.append_result(ts.cleanup.result, run_id)
            self._update_run()
            self._test_done(ts.cleanup.result.result)
            self.active_test += 1
            self.logger.info(f"Test '{ts.cleanup.config.name}' complete. Result: {ts.cleanup.result.result.name}")

    def run(self):
        if not self.active_dut or not self.active_program:
            raise ValueError("no program selected")

        if self.running:
            raise RuntimeError("Test already running")

        self.running = True
        self.abort_run = False

        self.run_thread = Thread(target=self._run)
        self.run_thread.start()

    def _get_run_thread_id(self) -> int:
        for id, thread in threading._active.items():
            if thread is self.run_thread:
                return id

    @staticmethod
    def _ctype_async_raise(target_tid, exception):
        ret = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(target_tid), ctypes.py_object(exception))
        if ret == 0:
            raise ValueError("Invalid thread ID")
        elif ret > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(target_tid, 0)
            raise SystemError("PyThreadState_SetAsyncExc failed")

    def wait_for_test_end(self):
        if self.running:
            self.run_thread.join()

    def _run(self):
        self.interface.emit_event(TesterRequest.LogClear.value)
        self.select_program(self.active_program.name, reset_attr=False)
        self._timer_update()
        self.logger.start_run(self.test_run.log)
        self.state['log'] = self.test_run.log
        self.attachment.set_run(self.test_run)

        self._reset_stats(total=len(self.test_run.test_results))
        self.active_test = 0
        self.test_run.start()
        run_id = self.db.append_run(self.test_run)
        self.test_run.run_id = run_id
        self._update_run()
        skip_all = False

        self.logger.info(f"Starting Program '{self.active_program.name}'. RunID: {run_id}")

        self._update_status(f"Executing {self.active_dut.name} Setup")
        if self.dut_setup:
            self._update_status(f"Executing Test Case '{self.dut_setup.config.name}'")
            self.dut_setup.execute()
            skip_all = self.dut_setup.result.result != TestResult.TestEval.PASS
            self.db.append_result(self.dut_setup.result, run_id)
            self._update_run()
            self._test_done(self.dut_setup.result.result)
            self.active_test += 1
            self.logger.info(f"Test '{self.dut_setup.config.name}' complete. Result: {self.dut_setup.result.result.name}")
        for ts in self.active_program.testsuites:
            if self.abort_run:
                skip_all = True
            self._execute_testsuite(ts, run_id, skip_all)

        self._update_status(f"Executing {self.active_dut.name} Cleanup")
        if self.dut_cleanup:
            self._update_status(f"Executing Test Case '{self.dut_cleanup.config.name}'")
            self.dut_cleanup.execute()
            skip_all = self.dut_cleanup.result.result != TestResult.TestEval.PASS
            self.db.append_result(self.dut_cleanup.result, run_id)
            self._update_run()
            self._test_done(self.dut_cleanup.result.result)
            self.active_test += 1
            self.logger.info(f"Test '{self.dut_cleanup.config.name}' complete. Result: {self.dut_cleanup.result.result.name}")

        self.running = False
        self.test_run.end()
        self._track_program_modifications()
        self._update_status("Idle")
        self.active_test = -1
        self._update_tester()
        self.logger.info(f"Program '{self.active_program.name}' done. RunID: {run_id}. Result: {self.test_run.result.name}")
        self.logger.stop_run()
        self.db.update_run_end(self.test_run)
        self.attachment.set_run(None)

    def _create_run(self):
        tester_info = {
            'name': self.name,
            'version': self.version
        }
        dut_info = {
            'name': self.active_dut.name,
            'description': self.active_dut.description,
            'product_id': self.active_dut.product_id,
            'image': self.active_dut.image,
        }
        # Extract program attributes from run_attr (which includes user modifications).
        # Program attributes = run_attr but exclude DUT-only attributes
        # (keys that exist in DUT but not in original program and have same value).
        program_attr = {}
        for key, value in self.run_attr.items():
            if key in self.active_program.attr:
                program_attr[key] = value
            elif key not in self.active_dut.attr:
                program_attr[key] = value
            elif self.run_attr.get(key) != self.active_dut.attr.get(key):
                program_attr[key] = value
        program_info = {
            'name': self.active_program.name,
            'description': self.active_program.description,
            'attr': program_attr
        }
        self.test_run = TestRun(tester_info, dut_info, program_info)

        self._store_original_skip_states()

        if self.dut_setup:
            self.dut_setup.config.attr = self.dut_setup.config.attr | self.run_attr
            self.test_run.append_result(self.dut_setup.result)

        for ts in self.active_program.testsuites:
            if ts.setup:
                ts.setup.config.attr = ts.setup.config.attr | self.run_attr
                self.test_run.append_result(ts.setup.result)
            for tc in ts.testcases:
                tc.config.attr = tc.config.attr | self.run_attr
                self.test_run.append_result(tc.result)
            if ts.cleanup:
                ts.cleanup.config.attr = ts.cleanup.config.attr | self.run_attr
                self.test_run.append_result(ts.cleanup.result)

        if self.dut_cleanup:
            self.dut_cleanup.config.attr = self.dut_cleanup.config.attr | self.run_attr
            self.test_run.append_result(self.dut_cleanup.result)

        self._update_run()

    def _store_original_skip_states(self):
        self.original_skip_states = {}
        original_program = next((p for p in self.active_dut.programs if p.name == self.active_program.name), None)
        if not original_program:
            return
        for ts in original_program.testsuites:
            if ts.setup:
                self.original_skip_states[f"{ts.name}_setup"] = ts.setup.config.skip
            for tc in ts.testcases:
                self.original_skip_states[f"{ts.name}_{tc.config.name}"] = tc.config.skip
            if ts.cleanup:
                self.original_skip_states[f"{ts.name}_cleanup"] = ts.cleanup.config.skip

    def _track_program_modifications(self):
        if not hasattr(self, 'original_skip_states'):
            return
        modifications = []
        for ts in self.active_program.testsuites:
            if ts.setup:
                test_id = f"{ts.name}_setup"
                original_skip = self.original_skip_states.get(test_id, False)
                final_skip = ts.setup.config.skip
                if original_skip != final_skip:
                    modifications.append({
                        'test_id': test_id,
                        'test_name': ts.setup.config.name,
                        'suite': ts.name,
                        'type': 'setup',
                        'original_skip': original_skip,
                        'final_skip': final_skip,
                        'action': 'disabled' if final_skip else 'enabled'
                    })
            for tc in ts.testcases:
                test_id = f"{ts.name}_{tc.config.name}"
                original_skip = self.original_skip_states.get(test_id, False)
                final_skip = tc.config.skip
                if original_skip != final_skip:
                    modifications.append({
                        'test_id': test_id,
                        'test_name': tc.config.name,
                        'suite': ts.name,
                        'type': 'testcase',
                        'original_skip': original_skip,
                        'final_skip': final_skip,
                        'action': 'disabled' if final_skip else 'enabled'
                    })
            if ts.cleanup:
                test_id = f"{ts.name}_cleanup"
                original_skip = self.original_skip_states.get(test_id, False)
                final_skip = ts.cleanup.config.skip
                if original_skip != final_skip:
                    modifications.append({
                        'test_id': test_id,
                        'test_name': ts.cleanup.config.name,
                        'suite': ts.name,
                        'type': 'cleanup',
                        'original_skip': original_skip,
                        'final_skip': final_skip,
                        'action': 'disabled' if final_skip else 'enabled'
                    })
        self.test_run.program_modified = len(modifications) > 0

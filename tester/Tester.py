import pathlib
import copy
import threading
from importlib.metadata import version
import pyjson5 as json
import os
import ctypes
from contextlib import suppress
from threading import Thread
from datetime import datetime, timedelta
from abc import ABC, abstractmethod, ABCMeta
from .TestSuite import TestSuite
from .TestDB import TestDB
from .TestProgram import TestProgram
from .TestRun import TestRun
from .TestResult import TestResult
from .TestReport import TestReport
from .TesterIf import TesterIf, TesterRequest
from .TesterConfig import TesterConfig
from .TestCase import TestCase
from .TestLogger import TestLogger
from .TestUtil import AbortRunException, TestDialog, TestAttachment
from .Dut import Dut

class Tester(ABC):
    __metaclass__ = ABCMeta
    DEFAULT_REPORT_PATH = './report.html'

    def __init__(self, config: TesterConfig) -> None:
        super().__init__()
        self.db = TestDB(config.db_config)
        self.setup = json.load(open(config.setup_file,'r'))
        self.name = config.name
        self.description = config.description
        self.version: str = config.version
        self.config = config
        self.dialog = TestDialog()
        self.attachment = TestAttachment()
        self.logger = TestLogger(name=self.name, dirname=config.log_dir)
        self.logger.info(f'Starting Tester {self.name}')
        self.assets = self._init(self.setup)
        self.duts = self.populate_duts(json.load(open(config.duts_file,'r')))
        self.duts_path = pathlib.Path(config.duts_file).parent.resolve()
        self.active_dut: Dut = None
        self.dut_setup: TestCase = None
        self.dut_cleanup: TestCase = None
        self.active_program: TestProgram = None
        self.test_run = None
        self.status_str = "Idle"
        self.running = False
        self.__reset_stats()
        self.active_test = -1
        self.abort_run = False
        self.run_thread = None

        # interface
        self.interface = TesterIf()
        self.interface.connect_handler = self._client_connected_handler
        self.interface.disconnect_handler = self._client_disconnected_handler
        self.interface.set_dut_handler = self._set_dut_handler
        self.interface.set_program_handler = self._set_program_handler
        self.interface.start_run_handler = self._start_run_handler
        self.interface.stop_run_handler = self._stop_run_handler
        self.interface.get_dut_image_handler = self._get_dut_image_handler
        self.interface.get_report_handler = self._get_report_handler
        self.interface.get_runs_handler = self._get_runs_handler
        self.interface.get_available_tests_handler = self._get_available_tests_handler
        self.interface.get_available_programs_handler = self._get_available_programs_handler
        self.interface.get_available_duts_handler = self._get_available_duts_handler
        self.interface.query_test_results_handler = self._query_test_results_handler
        self.interface.get_state_handler = self._get_state_handler
        self.interface.reload_handler = self._reload_handler
        self.interface.attr_handler = self._attr_handler
        self.interface.request_handler = self._request_handler
        self.interface.dialog_response_handler = self._dialog_response_handler
        self.interface.test_execute_state_handler = self._test_execute_state_handler
        self._generate_state()
        self.select_dut(next(iter(self.duts)).name)
        self.select_program(next(iter(self.active_dut.programs)).name)

        if config.ui is True:
            self.interface.run()

    def _timer_update(self):
        if self.running:
            self._update_tester()
            threading.Timer(0.5, self._timer_update).start()

    def _update_status(self, status: str):
        self.status_str = status
        self._update_tester()
        self.logger.info(status)

    def populate_duts(self, d):
        dut_list = []
        for dut in d['duts']:
            dut_list.append(Dut.from_dict(dut, self.assets, debug_reload=self.config.debug_reload))
        return dut_list

    def __reset_stats(self, total=0):
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

    def __test_done(self, result):
        self.test_stats['done'] += 1
        self.test_stats[result.name] += 1

    def select_program(self, program_name: str, reset_attr = True):
        if not self.active_dut:
            raise ValueError("No DUT selected")
        program = next((p for p in self.active_dut.programs if p.name == program_name), next(iter(p for p in self.active_dut.programs)))

        # Preserve user's checkbox states if we have an existing active_program
        user_skip_states = {}
        if hasattr(self, 'active_program') and self.active_program:
            for ts in self.active_program.testsuites:
                if ts.setup:
                    user_skip_states[f"{ts.name}_setup"] = ts.setup.config.skip
                for tc in ts.testcases:
                    user_skip_states[f"{ts.name}_{tc.config.name}"] = tc.config.skip
                if ts.cleanup:
                    user_skip_states[f"{ts.name}_cleanup"] = ts.cleanup.config.skip

        self.active_program = copy.deepcopy(program)
        self.dut_setup = copy.deepcopy(self.active_dut.setup)
        self.dut_cleanup = copy.deepcopy(self.active_dut.cleanup)

        # Restore user's checkbox states
        for ts in self.active_program.testsuites:
            if ts.setup and f"{ts.name}_setup" in user_skip_states:
                ts.setup.config.skip = user_skip_states[f"{ts.name}_setup"]
            for tc in ts.testcases:
                if f"{ts.name}_{tc.config.name}" in user_skip_states:
                    tc.config.skip = user_skip_states[f"{ts.name}_{tc.config.name}"]
            if ts.cleanup and f"{ts.name}_cleanup" in user_skip_states:
                ts.cleanup.config.skip = user_skip_states[f"{ts.name}_cleanup"]

        if reset_attr:
            # Program-level attributes should override existing ones (including DUT defaults)
            # Keep the rest of the attribute hierarchy unchanged
            self.run_attr = self.active_dut.attr | self.active_program.attr
        self._create_run()
        self.__reset_stats(total=len(self.test_run.test_results))
        self._update_program()
        self.logger.info(f"Selected program '{self.active_program.name}'")

    def select_dut(self, dut_name: str):
        program_name = self.active_program.name if self.active_program else None
        dut = next(d for d in self.duts if d.name == dut_name)
        self.active_dut = dut
        self.__reset_stats()
        self._update_dut()
        self.logger.info(f"Selected DUT '{self.active_dut.name}'")
        self.select_program(program_name=program_name)

    def _execute_testsuite(self, ts: TestSuite, run_id, skip_suite:bool=False):
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
            self._update_run(self.active_test)
            self.__test_done(ts.setup.result.result)
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
            self._update_run(self.active_test)
            self.__test_done(tc.result.result)
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
            self._update_run(self.active_test)
            self.__test_done(ts.cleanup.result.result)
            self.active_test += 1
            self.logger.info(f"Test '{ts.cleanup.config.name}' complete. Result: {ts.cleanup.result.result.name}")

    def run(self):
        # validate that we're ready
        if not self.active_dut or not self.active_program:
            raise ValueError("no program selected")

        if self.running:
            raise RuntimeError("Test already running")

        self.running = True
        self.abort_run = False

        self.run_thread = Thread(target = self._run)
        self.run_thread.start()

    def _get_run_thread_id(self) -> int:
        for id, thread in threading._active.items():
            if thread is self.run_thread:
                return id

    @staticmethod
    def _ctype_async_raise(target_tid, exception):
        ret = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(target_tid), ctypes.py_object(exception))
        # ref: http://docs.python.org/c-api/init.html#PyThreadState_SetAsyncExc
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
        TestLogger.start_run(self.test_run.log)
        self.state['log'] = self.test_run.log
        self.attachment.set_run(self.test_run)

        # iterate over test program items and execute
        self.__reset_stats(total=len(self.test_run.test_results))
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
            self._update_run(self.active_test)
            self.__test_done(self.dut_setup.result.result)
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
            self._update_run(self.active_test)
            self.__test_done(self.dut_cleanup.result.result)
            self.active_test += 1
            self.logger.info(f"Test '{self.dut_cleanup.config.name}' complete. Result: {self.dut_cleanup.result.result.name}")

        self.running = False

        self.test_run.end()

        # Compare final skip states with original to track modifications
        self._track_program_modifications()

        self._update_status("Idle")
        self.active_test = -1
        self._update_tester()
        self.logger.info(f"Program '{self.active_program.name}' done. RunID: {run_id}. Result: {self.test_run.result.name}")
        TestLogger.stop_run()
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
        # Extract program attributes from run_attr (which includes user modifications)
        # Program attributes = run_attr but exclude DUT-only attributes
        # (keys that exist in DUT but not in original program and have same value)
        program_attr = {}
        for key, value in self.run_attr.items():
            # Include if: key exists in original program OR value differs from DUT value
            # (user modifications override DUT values, so they're program attributes)
            if key in self.active_program.attr:
                # Key exists in original program - always include (even if also in DUT)
                program_attr[key] = value
            elif key not in self.active_dut.attr:
                # Key added by user (not in original program or DUT)
                program_attr[key] = value
            elif self.run_attr.get(key) != self.active_dut.attr.get(key):
                # User modified a DUT attribute, making it a program attribute
                program_attr[key] = value
            # Else: key is DUT-only (exists in DUT, not in program, unchanged) - exclude
        program_info = {
            'name': self.active_program.name,
            'description': self.active_program.description,
            'attr': program_attr
        }
        self.test_run = TestRun(tester_info, dut_info, program_info)

        # Store original skip states for comparison
        self._store_original_skip_states()

        if self.dut_setup:
            # Attribute precedence: Program(UI) > testcase > testsuite > program defaults
            # Apply UI/program attrs last so they override underlying settings
            self.dut_setup.config.attr = self.dut_setup.config.attr | self.run_attr
            self.test_run.append_result(self.dut_setup.result)

        for ts in self.active_program.testsuites:
            if ts.setup:
                # Apply UI/program attrs last so they override underlying settings
                ts.setup.config.attr = ts.setup.config.attr | self.run_attr
                self.test_run.append_result(ts.setup.result)

            for tc in ts.testcases:
                # Apply UI/program attrs last so they override underlying settings
                tc.config.attr = tc.config.attr | self.run_attr
                self.test_run.append_result(tc.result)

            if ts.cleanup:
                # Apply UI/program attrs last so they override underlying settings
                ts.cleanup.config.attr = ts.cleanup.config.attr | self.run_attr
                self.test_run.append_result(ts.cleanup.result)

        if self.dut_cleanup:
            # Apply UI/program attrs last so they override underlying settings
            self.dut_cleanup.config.attr = self.dut_cleanup.config.attr | self.run_attr
            self.test_run.append_result(self.dut_cleanup.result)

        self._update_run()

    def _client_connected_handler(self):
        self.interface.emit_event(TesterRequest.State.value, self.state)

    def _client_disconnected_handler(self):
        pass

    def _set_dut_handler(self, data):
        if data.get('dut', None):
            self.select_dut(data.get('dut'))

    def _set_program_handler(self, data):
        if data.get('program', None):
            self.select_program(data.get('program'))

    def _start_run_handler(self):
        self.run()

    def _stop_run_handler(self):
        if self.running and not self.abort_run:
            self.abort_run = True
            if TestCase.is_executing():
                self._ctype_async_raise(self._get_run_thread_id(), AbortRunException)

    def _get_dut_image_handler(self):
        path = self.duts_path.joinpath(self.active_dut.image)
        return path if os.path.isfile(path) else None

    def _get_report_handler(self, id=0):
        try:
            id = int(id)
            if id == 0:
                id = self.db.get_latest_run_id()

            run = self.db.get_run(id)
            report_name = f'report_{run.dut}_{run.program}_{run.start_date.strftime("%Y_%m_%d_%H_%M_%S")}'.replace(' ','_')
            return (TestReport(run).generate(), report_name)
        except ValueError:
            return ('','')

    def _get_runs_handler(self):
        return self.db.get_runs()

    def _get_available_tests_handler(self):
        return self.db.get_available_tests()

    def _get_available_programs_handler(self):
        return self.db.get_available_programs()

    def _get_available_duts_handler(self):
        return self.db.get_available_duts()

    def _query_test_results_handler(self, query_params):
        return self.db.query_test_results(query_params)

    def _get_state_handler(self):
        return self.state

    def _reload_handler(self):
        dut_name = self.active_dut.name if self.active_dut else next(iter(self.duts)).name
        program_name = self.active_program.name if self.active_program else None
        self.duts = self.populate_duts(json.load(open(self.config.duts_file,'r')))
        self.active_dut: Dut = None
        self.dut_setup: TestCase = None
        self.dut_cleanup: TestCase = None
        self.active_program: TestProgram = None
        self.test_run = None
        self.select_dut(dut_name)
        self.select_program(program_name)
        self._generate_state()
        self.interface.emit_event(TesterRequest.State.value, self.state)

    def _attr_handler(self,attr):
        # sync only if this makes a difference (to avoid endless update loop)
        if self.run_attr | attr != self.run_attr:
            self.run_attr |= attr
            self._update_program()

    def _dialog_response_handler(self, rsp, data):
        self.dialog.close(rsp, data)

    def _test_execute_state_handler(self, data):
        """Handle test execution state changes from frontend"""
        test_id = data.get('test_id')
        execute = data.get('execute', True)
        test_type = data.get('type', 'testcase')

        if not self.active_program or not test_id:
            return

        # Update the skip state of the corresponding test case
        for ts in self.active_program.testsuites:
            if test_type == 'setup' and ts.setup and f"{ts.name}_setup" == test_id:
                ts.setup.config.skip = not execute
                # Setup controls cleanup and test cases
                if ts.cleanup:
                    ts.cleanup.config.skip = not execute
                for tc in ts.testcases:
                    tc.config.skip = not execute
                break
            elif test_type == 'cleanup' and ts.cleanup and f"{ts.name}_cleanup" == test_id:
                ts.cleanup.config.skip = not execute
                # Cleanup controls setup and test cases
                if ts.setup:
                    ts.setup.config.skip = not execute
                for tc in ts.testcases:
                    tc.config.skip = not execute
                break
            elif test_type == 'testcase':
                for tc in ts.testcases:
                    if f"{ts.name}_{tc.config.name}" == test_id:
                        tc.config.skip = not execute
                        break

        # Update the program state and broadcast to all clients
        self._update_program(emit=True)

        # Broadcast the change to all connected clients
        self.interface.emit_event(TesterRequest.TestExecuteState.value, data)

    def _request_handler(self, req):
        cmd = req.get('cmd', None)

        if cmd == 'run':
            dut = req.get('dut', "")
            program = req.get('program', "")
            attr = req.get('attr', {})

            if self.running:
                return {"code": 500, "data": "Tester Already Running"}

            try:
                self.select_dut(dut)
            except:
                return {"code": 500, "data": f"DUT {dut} not found"}

            try:
                self.select_program(program)
            except:
                return {"code": 500, "data": f"Program {program} not found for DUT {dut}"}

            self._attr_handler(attr)
            self.run()
            return {"code": 200, "data": f"Running DUT {dut} Program {program}"}

        elif cmd == 'stop':
            if not self.running:
                return {"code": 500, "data": "Tester Not Running"}
            else:
                self._stop_run_handler()
                return {"code": 200, "data": "Stopping"}

    @abstractmethod
    def _init(self, setup: dict) -> dict:
        pass

    def _update_tester(self, emit=True):
        if self.test_run and self.test_run.start_date:
            if self.running:
                elapsed = datetime.now()-self.test_run.start_date
            else:
                elapsed = self.test_run.end_date-self.test_run.start_date
        else:
            elapsed = timedelta(seconds=0)

        self.state['tester'] = {
            "version": self.version,
            "fw_version": version("tester"),
            "active_test": self.active_test,
            "name": self.name,
            "description": self.description,
            "running": self.running,
            "text": self.status_str,
            "elapsed": str(timedelta(seconds=elapsed.seconds)),
            "total": self.test_stats['total'],
            "done": self.test_stats['done'],
            "pass": self.test_stats['PASS'],
            "fail": self.test_stats['FAIL'],
            "error": self.test_stats['ERROR'],
            "skip": self.test_stats['SKIPPED'],
            "aborted": self.test_stats['ABORTED'],
            "dialog": self.dialog.encode(),
        }
        if emit:
            self.interface.emit_event(TesterRequest.Tester.value, self.state['tester'])

    def _update_duts(self, emit=True):
        self.state['duts'] = [d.name for d in self.duts]
        self._update_tester(emit)
        if emit:
            self.interface.emit_event(TesterRequest.State.value, self.state)

    def _update_programs(self, emit=True):
        if self.active_dut:
            self.state['programs'] = [p.name for p in self.active_dut.programs]
            self._update_tester(emit)
            if emit:
                self.interface.emit_event(TesterRequest.State.value, self.state)

    def _update_dut(self, emit=True):
        if self.active_dut:
            self.state['dut'] = {
                "name": self.active_dut.name,
                "description": self.active_dut.description,
                "product_id": self.active_dut.product_id,
            }
            self._update_tester(emit)
            self._update_programs(emit)
            if emit:
                self.interface.emit_event(TesterRequest.ActiveDut.value, self.state['dut'])

    def _update_program(self, emit=True):
        if self.active_program:
            # Build test case configuration list
            test_cases = []
            for ts in self.active_program.testsuites:
                if ts.setup:
                    test_cases.append({
                        "id": f"{ts.name}_setup",
                        "suite": ts.name,
                        "name": ts.setup.config.name,
                        "type": "setup",
                        "execute": not ts.setup.config.skip
                    })

                for tc in ts.testcases:
                    test_cases.append({
                        "id": f"{ts.name}_{tc.config.name}",
                        "suite": ts.name,
                        "name": tc.config.name,
                        "type": "testcase",
                        "execute": not tc.config.skip
                    })

                if ts.cleanup:
                    test_cases.append({
                        "id": f"{ts.name}_cleanup",
                        "suite": ts.name,
                        "name": ts.cleanup.config.name,
                        "type": "cleanup",
                        "execute": not ts.cleanup.config.skip
                    })

            self.state['program'] = {
                    "name": self.active_program.name,
                    "description": self.active_program.description,
                    "attr": self.run_attr,
                    "attr_schema": self.active_program.attr_schema,
                    "test_cases": test_cases
                }
            self._update_tester(emit)
            if emit:
                self.interface.emit_event(TesterRequest.ActiveProgram.value, self.state['program'])

    def _update_run(self, idx=None, emit=True):
        if self.test_run:
            if False and (idx is not None):
                self.state['run'][idx] = self.test_run.test_results[idx].to_dict()
                t = self.state['run'][idx]
                if t['Result'] != 'UNKNOWN' and self.test_run.start_date:
                    t['Time'] = str(timedelta(seconds=(t['Time']-self.test_run.start_date).seconds))
                else:
                    t['Time'] = str(timedelta(seconds=0))
                if emit:
                    self.interface.emit_event(TesterRequest.RunItem.value, {"idx": idx, "item": self.state['run'][idx]})
            else:
                self.state['run'] = [t.to_dict() for t in self.test_run.test_results]
                for t in self.state['run']:
                    if t['Result'] != 'UNKNOWN' and self.test_run.start_date:
                        t['Time'] = str(timedelta(seconds=(t['Time']-self.test_run.start_date).seconds))
                    else:
                        t['Time'] = str(timedelta(seconds=0))
                if emit:
                    self.interface.emit_event(TesterRequest.RunState.value, self.state['run'])
        else:
            self.state['run'] = []
            if emit:
                self.interface.emit_event(TesterRequest.RunState.value, self.state['run'])

    def _generate_state(self) -> dict:
        self.state = {}
        emit = True
        self._update_duts(emit)
        self._update_programs(emit)
        self._update_dut(emit)
        self._update_program(emit)
        self._update_tester(emit)
        self._update_run(emit=emit)
        self.state['log'] = self.test_run.log if self.test_run else []

    def _store_original_skip_states(self):
        """Store the original skip states from the program definition"""
        self.original_skip_states = {}

        # Get the original program definition (before user modifications)
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
        """Compare final skip states with original to track user modifications"""
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

        # Set the program_modified flag
        self.test_run.program_modified = len(modifications) > 0

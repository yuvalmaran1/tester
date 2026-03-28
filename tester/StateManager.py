"""StateManagerMixin — UI state management logic extracted from Tester.

Contains all methods responsible for building and pushing UI state:
  - Tester-level state (_update_tester, _timer_update, _update_status)
  - DUT / program / run slice updates (_update_duts, _update_programs,
    _update_dut, _update_program, _update_run)
  - Full state rebuild (_generate_state)
"""

import threading
from datetime import datetime, timedelta
from importlib.metadata import version

from .TesterIf import TesterRequest


class StateManagerMixin:
    """Mixin providing UI state management for Tester.

    Expects the host class to supply the following attributes on self:
    state, test_run, running, active_dut, active_program, duts,
    run_attr, status_str, test_stats, version, name, description,
    dialog, interface, logger.
    """

    def _timer_update(self):
        if self.running:
            self._update_tester()
            threading.Timer(0.5, self._timer_update).start()

    def _update_status(self, status: str):
        self.status_str = status
        self._update_tester()
        self.logger.info(status)

    def _update_tester(self, emit=True):
        if self.test_run and self.test_run.start_date:
            if self.running:
                elapsed = datetime.now() - self.test_run.start_date
            else:
                elapsed = self.test_run.end_date - self.test_run.start_date
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
            "operator": self.current_operator,
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

    def _update_run(self, emit=True):
        if self.test_run:
            self.state['run'] = [t.to_dict() for t in self.test_run.test_results]
            for t in self.state['run']:
                if t['Result'] != 'UNKNOWN' and self.test_run.start_date:
                    t['Time'] = str(timedelta(seconds=(t['Time'] - self.test_run.start_date).seconds))
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

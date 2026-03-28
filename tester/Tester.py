import hashlib
import pathlib
import copy
import pyjson5 as json
import os
import ctypes
from threading import Thread
from datetime import datetime, timedelta
from abc import ABC, abstractmethod, ABCMeta
from .TestDB import TestDB
from .TestProgram import TestProgram
from .TestResult import TestResult
from .TestReport import TestReport
from .TesterIf import TesterIf, TesterRequest
from .TesterConfig import TesterConfig
from .StationConfig import StationConfig
from .TestCase import TestCase
from .TestLogger import TestLogger
from .TestUtil import AbortRunException, TestDialog, TestAttachment
from .Dut import Dut
from .RunExecutor import RunExecutorMixin
from .StateManager import StateManagerMixin
from .Operator import hash_password, verify_password

class Tester(RunExecutorMixin, StateManagerMixin, ABC):
    __metaclass__ = ABCMeta
    DEFAULT_REPORT_PATH = './report.html'

    def __init__(self, config: TesterConfig) -> None:
        super().__init__()
        self.db = TestDB(config.db_config)
        self.name = config.name
        self.description = config.description
        self.version: str = config.version
        self.config = config
        self.dialog = TestDialog()
        self.attachment = TestAttachment()
        self.logger = TestLogger(name=self.name, dirname=config.log_dir)
        self.logger.info(f'Starting Tester {self.name}')

        raw_station = json.load(open(config.station_config_file, 'r'))
        station_cls = config.station_config_class or StationConfig
        self.station_config: StationConfig = station_cls.model_validate(raw_station)

        self.assets = self._init(self.station_config)
        self.duts = self.populate_duts(json.load(open(config.duts_file,'r')))
        with open(config.duts_file, 'rb') as _f:
            self.config_hash = hashlib.sha256(_f.read()).hexdigest()
        self.duts_path = pathlib.Path(config.duts_file).parent.resolve()
        self.active_dut: Dut = None
        self.dut_setup: TestCase = None
        self.dut_cleanup: TestCase = None
        self.active_program: TestProgram = None
        self.test_run = None
        self.status_str = "Idle"
        self.running = False
        self._reset_stats()
        self.active_test = -1
        self.abort_run = False
        self.serial_number = ''
        self.run_thread = None
        self.current_operator = None  # dict with id/username/display_name/role or None

        # Seed admin and resolve initial operator
        self._seed_admin()
        if not config.require_login:
            self.current_operator = self.db.get_operator_by_username('admin')
            if self.current_operator:
                # Strip password_hash for safety
                self.current_operator = {k: v for k, v in self.current_operator.items() if k != 'password_hash'}

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
        self.interface.login_handler = self._login_handler
        self.interface.logout_handler = self._logout_handler
        self.interface.list_operators_handler = self._list_operators_handler
        self.interface.add_operator_handler = self._add_operator_handler
        self.interface.update_operator_handler = self._update_operator_handler
        self.interface.delete_operator_handler = self._delete_operator_handler
        self.interface.update_operator_password_handler = self._update_operator_password_handler
        self.interface.set_serial_handler = self._set_serial_handler
        self._generate_state()
        self.select_dut(next(iter(self.duts)).name)
        self.select_program(next(iter(self.active_dut.programs)).name)

        if config.ui is True:
            self.interface.run()

    def populate_duts(self, d):
        dut_list = []
        for dut in d['duts']:
            dut_list.append(Dut.from_dict(dut, self.assets, debug_reload=self.config.debug_reload))
        return dut_list

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
        # sn_generator is stateful (counter) — preserve the original instance
        # so state (e.g. sequential counter) is maintained across runs.
        self.active_program.sn_generator = program.sn_generator
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
            # Pre-fill serial number with the program's default (operator can still override)
            self.serial_number = self.active_program.default_serial_number
            self._update_tester(emit=False)
        self._create_run()
        self._reset_stats(total=len(self.test_run.test_results))
        self._update_program()
        self.logger.info(f"Selected program '{self.active_program.name}'")

    def select_dut(self, dut_name: str):
        program_name = self.active_program.name if self.active_program else None
        dut = next(d for d in self.duts if d.name == dut_name)
        self.active_dut = dut
        self._reset_stats()
        self._update_dut()
        self.logger.info(f"Selected DUT '{self.active_dut.name}'")
        self.select_program(program_name=program_name)

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
        if self.config.require_login and (not self.current_operator or self.current_operator.get('role') != 'admin'):
            return
        dut_name = self.active_dut.name if self.active_dut else next(iter(self.duts)).name
        program_name = self.active_program.name if self.active_program else None
        self.duts = self.populate_duts(json.load(open(self.config.duts_file,'r')))
        with open(self.config.duts_file, 'rb') as _f:
            self.config_hash = hashlib.sha256(_f.read()).hexdigest()
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

    def _set_serial_handler(self, data):
        self.serial_number = (data or {}).get('serial_number', '')
        self._update_tester()

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

    # ── Operator / authentication helpers ────────────────────────────────────

    def _seed_admin(self):
        """Create default admin account if no operators exist."""
        if not self.db.list_operators():
            self.db.add_operator(
                username='admin',
                display_name='Administrator',
                password_hash=hash_password('admin'),
                role='admin',
            )
            self.logger.info("Created default admin account (username: admin, password: admin)")

    def _login_handler(self, data):
        username = (data or {}).get('username', '')
        password = (data or {}).get('password', '')
        op = self.db.get_operator_by_username(username)
        if op and op.get('active') and verify_password(password, op.get('password_hash', '')):
            self.current_operator = {k: v for k, v in op.items() if k != 'password_hash'}
            self._update_tester()
            self.interface.emit_event(TesterRequest.LoginResult.value, {'success': True, 'operator': self.current_operator})
            self.logger.info(f"Operator '{username}' logged in")
        else:
            self.interface.emit_event(TesterRequest.LoginResult.value, {'success': False, 'error': 'Invalid username or password'})

    def _logout_handler(self):
        if self.current_operator:
            self.logger.info(f"Operator '{self.current_operator['username']}' logged out")
        self.current_operator = None
        self._update_tester()

    def _list_operators_handler(self):
        if not self.current_operator or self.current_operator.get('role') != 'admin':
            return
        ops = self.db.list_operators()
        self.interface.emit_event(TesterRequest.OperatorList.value, ops)

    def _add_operator_handler(self, data):
        if not self.current_operator or self.current_operator.get('role') != 'admin':
            return
        username = (data or {}).get('username', '').strip()
        display_name = (data or {}).get('display_name', '').strip()
        password = (data or {}).get('password', '')
        role = (data or {}).get('role', 'operator')
        if not username or not password:
            return
        try:
            self.db.add_operator(username, display_name or username, hash_password(password), role)
            self.interface.emit_event(TesterRequest.OperatorList.value, self.db.list_operators())
        except Exception as e:
            self.logger.error(f"Failed to add operator '{username}': {e}")

    def _update_operator_handler(self, data):
        if not self.current_operator or self.current_operator.get('role') != 'admin':
            return
        op_id = (data or {}).get('id')
        display_name = (data or {}).get('display_name', '')
        role = (data or {}).get('role', 'operator')
        active = (data or {}).get('active', True)
        if op_id is None:
            return
        self.db.update_operator(op_id, display_name, role, active)
        self.interface.emit_event(TesterRequest.OperatorList.value, self.db.list_operators())

    def _delete_operator_handler(self, data):
        if not self.current_operator or self.current_operator.get('role') != 'admin':
            return
        op_id = (data or {}).get('id')
        if op_id is None:
            return
        # Prevent deleting own account
        if self.current_operator.get('id') == op_id:
            return
        self.db.delete_operator(op_id)
        self.interface.emit_event(TesterRequest.OperatorList.value, self.db.list_operators())

    def _update_operator_password_handler(self, data):
        if not self.current_operator:
            return
        op_id = (data or {}).get('id')
        password = (data or {}).get('password', '')
        if op_id is None or not password:
            return
        # Operators can only change their own password; admins can change any
        if self.current_operator.get('role') != 'admin' and self.current_operator.get('id') != op_id:
            return
        self.db.update_operator_password(op_id, hash_password(password))

    @abstractmethod
    def _init(self, station_config: StationConfig) -> dict:
        pass

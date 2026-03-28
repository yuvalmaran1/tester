from flask import Flask, Response, request, send_file, \
                  send_from_directory, render_template, stream_with_context
from flask_socketio import SocketIO
from enum import Enum
import pathlib
import pyjson5 as json
from time import sleep
from .TestLogger import TestLogger
from logging import StreamHandler

DUT_IMAGE_PATH = pathlib.Path(__file__).parent.resolve().joinpath('Assets').joinpath('dut.png')
FRONTEND_BUILD_PATH = pathlib.Path(__file__).parent.joinpath('frontend')
FRONTEND_TEMPLATE_PATH = FRONTEND_BUILD_PATH
FRONTEND_STATIC_PATH = FRONTEND_BUILD_PATH.joinpath('_next').joinpath('static') #
FRONTEND_MEDIA_PATH = FRONTEND_STATIC_PATH.joinpath('media')

class EndpointAction(object):
    def __init__(self, action):
        self.action = action

    def __call__(self, *args, **kwargs):
        # Perform the action
        answer = self.action(**kwargs)

        if isinstance(answer, Response):
            self.response = answer
        else:
            self.response = Response(answer, status=200, headers={})

        # Send it
        return self.response

class TesterRequest(Enum):
    GetState = "get_state"
    State = "state"
    Tester = "tester"
    Log = "log"
    LogClear = "log_clear"
    ActiveDut = "active_dut"
    ActiveProgram = "active_program"
    RunState = "run"
    RunItem = "run_item"
    SetDut = "set_dut"
    SetProgram = "set_program"
    StartRun = "start_run"
    StopRun = "stop_run"
    Reload = "reload"
    Attr = "attr"
    TestExecuteState = "test_execute_state"
    DialogResponse = "dialog_response"
    Login = "login"
    Logout = "logout"
    LoginResult = "login_result"
    ListOperators = "list_operators"
    AddOperator = "add_operator"
    UpdateOperator = "update_operator"
    DeleteOperator = "delete_operator"
    UpdateOperatorPassword = "update_operator_password"
    OperatorList = "operator_list"

class TesterIf:
    def __init__(self) -> None:
        self.app = Flask('tester',template_folder=FRONTEND_TEMPLATE_PATH, static_folder=FRONTEND_STATIC_PATH)
        self.app.config['EXPLAIN_TEMPLATE_LOADING'] = True

        self.sio = SocketIO(self.app, async_mode='threading')
        self.connect_handler = None
        self.disconnect_handler = None
        self.start_run_handler = None
        self.stop_run_handler = None
        self.set_dut_handler = None
        self.set_program_handler = None
        self.get_dut_image_handler = None
        self.get_report_handler = None
        self.get_runs_handler = None
        self.get_state_handler = None
        self.reload_handler = None
        self.attr_handler = None
        self.request_handler = None
        self.dialog_response_handler = None
        self.test_execute_state_handler = None
        self.get_available_tests_handler = None
        self.get_available_programs_handler = None
        self.get_available_duts_handler = None
        self.query_test_results_handler = None
        self.login_handler = None
        self.logout_handler = None
        self.list_operators_handler = None
        self.add_operator_handler = None
        self.update_operator_handler = None
        self.delete_operator_handler = None
        self.update_operator_password_handler = None
        self.register_request('connect', self._connect_handler)
        self.register_request('disconnect', self._disconnect_handler)
        self.register_request(TesterRequest.StartRun.value, self._start_run_handler)
        self.register_request(TesterRequest.StopRun.value, self._stop_run_handler)
        self.register_request(TesterRequest.SetDut.value, self._set_dut_handler)
        self.register_request(TesterRequest.SetProgram.value, self._set_program_handler)
        self.register_request(TesterRequest.GetState.value, self._get_state_handler)
        self.register_request(TesterRequest.Reload.value, self._reload_handler)
        self.register_request(TesterRequest.Attr.value, self._attr_handler)
        self.register_request(TesterRequest.TestExecuteState.value, self._test_execute_state_handler)
        self.register_request(TesterRequest.DialogResponse.value, self._dialog_response_handler)
        self.register_request(TesterRequest.Login.value, self._login_handler)
        self.register_request(TesterRequest.Logout.value, self._logout_handler)
        self.register_request(TesterRequest.ListOperators.value, self._list_operators_handler)
        self.register_request(TesterRequest.AddOperator.value, self._add_operator_handler)
        self.register_request(TesterRequest.UpdateOperator.value, self._update_operator_handler)
        self.register_request(TesterRequest.DeleteOperator.value, self._delete_operator_handler)
        self.register_request(TesterRequest.UpdateOperatorPassword.value, self._update_operator_password_handler)
        self._add_endpoints()
        log_handler = SocketLogHandler(self)
        log_handler.setFormatter(TestLogger._fmt)
        TestLogger().addHandler(log_handler)

    def run(self):
        self.sio.run(self.app, host='0.0.0.0', port=5050, use_reloader=False, allow_unsafe_werkzeug=True)

    def _add_endpoints(self):
        self._add_endpoint(endpoint='/', endpoint_name='/', handler=self.index_handler)
        self._add_endpoint(endpoint='/results', endpoint_name='/results', handler=self.results_handler)
        self._add_endpoint(endpoint='/test-query', endpoint_name='/test-query', handler=self.test_query_handler)
        self._add_endpoint(endpoint='/admin', endpoint_name='/admin', handler=self.admin_handler)
        self._add_endpoint(endpoint='/manifest.json', endpoint_name='/manifest.json', handler=self.manifest_handler)
        self._add_endpoint(endpoint='/favicon.ico', endpoint_name='/favicon.ico', handler=self.favicon_handler)
        self._add_endpoint(endpoint='/<path:path>', endpoint_name='/<path:path>', handler=self.file_handler)
        self._add_endpoint(endpoint='/dut_image', endpoint_name='/dut_image', handler=self._get_dut_image_handler)
        self._add_endpoint(endpoint='/get_report', endpoint_name='/get_report', handler=self._get_report_handler)
        self._add_endpoint(endpoint='/get_runs', endpoint_name='/get_runs', handler=self._get_runs_handler)
        self._add_endpoint(endpoint='/generate_report/<id>', endpoint_name='/generate_report/<id>', handler=self._generate_report_handler)
        self._add_endpoint(endpoint='/show_report/<id>', endpoint_name='/show_report/<id>', handler=self._show_report_handler)
        self._add_endpoint(endpoint='/get_available_tests', endpoint_name='/get_available_tests', handler=self._get_available_tests_handler)
        self._add_endpoint(endpoint='/get_available_programs', endpoint_name='/get_available_programs', handler=self._get_available_programs_handler)
        self._add_endpoint(endpoint='/get_available_duts', endpoint_name='/get_available_duts', handler=self._get_available_duts_handler)
        self._add_endpoint(endpoint='/query_test_results', endpoint_name='/query_test_results', handler=self._query_test_results_handler)
        self._add_endpoint(endpoint='/req/', endpoint_name='/req/', methods = ['GET', 'POST'], handler=self._request_handler)

    def _add_endpoint(self, endpoint=None, endpoint_name=None, handler=None, methods=None):
        self.app.add_url_rule(endpoint, endpoint_name, EndpointAction(handler), methods=methods)

    def register_request(self, req: str, handler):
        self.sio.on_event(req, handler=handler)

    def emit_event(self, evt: str, payload: dict = None):
        self.sio.emit(evt, payload)

    def index_handler(self):
        return render_template("index.html")

    def results_handler(self):
        return render_template("results.html")

    def test_query_handler(self):
        return render_template("test-query.html")

    def admin_handler(self):
        return render_template("admin.html")

    def favicon_handler(self):
        return send_from_directory(FRONTEND_BUILD_PATH, 'icon.svg', mimetype='image/svg+xml')

    def manifest_handler(self):
        return send_from_directory(FRONTEND_BUILD_PATH, 'build-manifest.json')

    def file_handler(self, path):
        return send_from_directory(FRONTEND_BUILD_PATH, path)

    def _get_report_handler(self):
        if self.get_report_handler:
            report_str, report_name = self.get_report_handler()
            return Response(report_str,
                            mimetype="text/json",
                            headers={"Content-disposition":
                                f"attachment; filename={report_name}.html"})

    def _get_runs_handler(self):
        if self.get_runs_handler:
            runs = self.get_runs_handler()
            return Response(runs, mimetype="text/json")

    def _generate_report_handler(self, id):
        if self.get_report_handler:
            report_str, report_name = self.get_report_handler(id)
            return Response(report_str,
                            mimetype="text/html",
                            headers={"Content-disposition":
                                f"attachment; filename={report_name}.html"})

    def _show_report_handler(self, id):
        if self.get_report_handler:
            report_str, _ = self.get_report_handler(id)
            return Response(report_str, mimetype="text/html")

    def _request_handler(self):
        if request.method == 'GET':
            state = self.get_state_handler()
            return Response(json.dumps(state["tester"]), mimetype="text/json")
        elif request.method == 'POST' and self.request_handler:
            rsp = self.request_handler(request.json)
            if rsp:
                return Response(rsp["data"], status=rsp["code"], mimetype="text/plain")

    def _get_dut_image_handler(self):
        img = None
        if self.get_dut_image_handler:
            img = self.get_dut_image_handler()
        if img is None:
            img = DUT_IMAGE_PATH

        return send_file(img, mimetype='image/png')

    def _get_available_tests_handler(self):
        if self.get_available_tests_handler:
            tests = self.get_available_tests_handler()
            return Response(json.dumps(tests), mimetype="text/json")
        return Response(json.dumps([]), mimetype="text/json")

    def _get_available_programs_handler(self):
        if self.get_available_programs_handler:
            programs = self.get_available_programs_handler()
            return Response(json.dumps(programs), mimetype="text/json")
        return Response(json.dumps([]), mimetype="text/json")

    def _get_available_duts_handler(self):
        if self.get_available_duts_handler:
            duts = self.get_available_duts_handler()
            return Response(json.dumps(duts), mimetype="text/json")
        return Response(json.dumps([]), mimetype="text/json")

    def _query_test_results_handler(self):
        if self.query_test_results_handler:
            try:
                # Get query parameters - support both old and new parameter names
                test_name = request.args.get('test_name')
                test_names = request.args.get('test_names')
                program = request.args.get('program')
                programs = request.args.get('programs')
                dut = request.args.get('dut')
                duts = request.args.get('duts')
                result = request.args.get('result')
                results = request.args.get('results')
                start_date = request.args.get('start_date')
                end_date = request.args.get('end_date')

                # Build query parameters dict - prefer new parameter names
                query_params = {
                    'test_names': test_names,
                    'test_name': test_name,  # fallback for backward compatibility
                    'programs': programs,
                    'program': program,  # fallback for backward compatibility
                    'duts': duts,
                    'dut': dut,  # fallback for backward compatibility
                    'results': results,
                    'result': result,  # fallback for backward compatibility
                    'start_date': start_date,
                    'end_date': end_date
                }

                # Remove None values
                query_params = {k: v for k, v in query_params.items() if v is not None}

                results = self.query_test_results_handler(query_params)
                return Response(json.dumps(results), mimetype="text/json")
            except Exception as e:
                print(f"Error in query_test_results_handler: {e}")
                return Response(json.dumps({"error": str(e)}), mimetype="text/json", status=500)
        return Response(json.dumps([]), mimetype="text/json")

    def _connect_handler(self, event):
        if self.connect_handler:
            self.connect_handler()

    def _disconnect_handler(self):
        if self.disconnect_handler:
            self.disconnect_handler()

    def _start_run_handler(self):
        if self.start_run_handler:
            self.start_run_handler()

    def _stop_run_handler(self):
        if self.stop_run_handler:
            self.stop_run_handler()

    def _set_dut_handler(self, data):
        if self.set_dut_handler:
            self.set_dut_handler(data)

    def _set_program_handler(self, data):
        if self.set_program_handler:
            self.set_program_handler(data)

    def _get_state_handler(self):
        if self.get_state_handler:
            state = self.get_state_handler()
            self.emit_event(TesterRequest.State.value, state)

    def _reload_handler(self):
        if self.reload_handler:
            self.reload_handler()

    def _attr_handler(self, attr):
        if self.attr_handler:
            self.attr_handler(attr)

    def _test_execute_state_handler(self, data):
        if self.test_execute_state_handler:
            self.test_execute_state_handler(data)

    def _dialog_response_handler(self, response, data):
        if self.dialog_response_handler:
            self.dialog_response_handler(response, data)

    def _login_handler(self, data):
        if self.login_handler:
            self.login_handler(data)

    def _logout_handler(self):
        if self.logout_handler:
            self.logout_handler()

    def _list_operators_handler(self):
        if self.list_operators_handler:
            self.list_operators_handler()

    def _add_operator_handler(self, data):
        if self.add_operator_handler:
            self.add_operator_handler(data)

    def _update_operator_handler(self, data):
        if self.update_operator_handler:
            self.update_operator_handler(data)

    def _delete_operator_handler(self, data):
        if self.delete_operator_handler:
            self.delete_operator_handler(data)

    def _update_operator_password_handler(self, data):
        if self.update_operator_password_handler:
            self.update_operator_password_handler(data)


class SocketLogHandler(StreamHandler):
    def __init__(self, interface):
        StreamHandler.__init__(self)
        self.interface = interface

    def emit(self, record):
        msg = self.format(record) + '\n'
        self.interface.emit_event(TesterRequest.Log.value, msg)

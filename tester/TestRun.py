import os
import io
import zipfile
from .TestResult import TestResult
from .TestResultFactory import TestResultFactory
from datetime import datetime

class TestRun:
    def __init__(self, tester: dict, dut: dict, program: dict) -> None:
        self.tester = tester.get('name', '')
        self.tester_ver = tester.get('version', '')
        self.dut = dut.get('name', '')
        self.dut_desc = dut.get('description', '')
        self.dut_product_id = dut.get('product_id','')
        self.dut_image = dut.get('image','')
        self.program = program.get('name','')
        self.program_desc = program.get('description', '')
        self.program_attr = program.get('attr', {})  # Store program attributes
        self.start_date: datetime = None
        self.end_date: datetime = None
        self.result = TestResult.TestEval.UNKNOWN
        self.test_results = []
        self.run_id = None
        self.log = []
        self.attachment = io.BytesIO()
        self.attachments_exist = False
        self.program_modified = False  # Boolean flag indicating if program was modified
        self.operator = ''            # Username of the operator who started the run
        self.serial_number = ''       # unit serial number entered before the run
        self.config_hash = ''         # SHA-256 of duts.json at run time

    def start(self):
        self.start_date = datetime.now(tz=None)

    def end(self):
        self.end_date = datetime.now(tz=None)
        self.evaluate()

    def append_result(self, result: TestResult):
        self.test_results.append(result)

    def attachment_exists(self):
        return self.attachments_exist

    def get_attachment(self) -> bytes:
        return self.attachment.getvalue()

    def append_attachment_file(self, file_path: str):
        zipfile_mode = 'a' if self.attachments_exist else 'w'
        with open(file_path, 'rb') as file:
            file_data = file.read()
            with zipfile.ZipFile(self.attachment, zipfile_mode, zipfile.ZIP_LZMA) as zip_obj:
                zip_info = zipfile.ZipInfo(os.path.basename(file_path))
                zip_obj.writestr(zip_info, file_data, zipfile.ZIP_LZMA)
        self.attachments_exist = True

    def append_attachment_buffer(self, data, file_name: str):
        zipfile_mode = 'a' if self.attachments_exist else 'w'
        with zipfile.ZipFile(self.attachment, zipfile_mode, zipfile.ZIP_LZMA) as zip_obj:
            zip_obj.writestr(file_name, data, zipfile.ZIP_LZMA)
        self.attachments_exist = True

    def evaluate(self):
        res_counter = {i: 0 for i in TestResult.TestEval}
        for res in self.test_results:
            res_counter[res.result] += 1

        if res_counter[TestResult.TestEval.ABORTED] > 0:
            self.result = TestResult.TestEval.ABORTED
        elif res_counter[TestResult.TestEval.FAIL] > 0:
            self.result = TestResult.TestEval.FAIL
        elif res_counter[TestResult.TestEval.ERROR] > 0:
            self.result = TestResult.TestEval.ERROR
        elif res_counter[TestResult.TestEval.PASS] > 0:
            self.result = TestResult.TestEval.PASS
        else:
            self.result = TestResult.TestEval.UNKNOWN

    @staticmethod
    def from_dict(d, tests):
        tester = {
            "name": d['tester'],
            "version": d['tester_ver']
        }
        dut = {
            "name": d['dut'],
            "description": d['dut_desc'],
            "product_id": d['dut_product_id'],
            "image": d['dut_image']
        }
        program = {
            "name": d['program'],
            "description": d['program_desc'],
            "attr": d.get('program_attr', {})
        }

        run = TestRun(tester=tester, dut=dut, program=program)
        run.start_date = datetime.strptime(d['start_date'], '%Y-%m-%d %H:%M:%S.%f')
        run.end_date = datetime.strptime(d['end_date'], '%Y-%m-%d %H:%M:%S.%f')
        run.result = TestResult.TestEval[d['result']]

        for t in tests:
            res = TestResultFactory().from_dict(t)
            run.append_result(res)

        run.log = d['log']
        if d['attachment']:
            run.attachment.write(d['attachment'])
        run.attachments_exist = len(run.attachment.getbuffer()) > 0
        run.program_modified = d.get('program_modified', False)
        run.operator = d.get('operator', '')
        run.serial_number = d.get('serial_number', '')
        run.config_hash = d.get('config_hash', '')

        return run

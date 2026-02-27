from .TestResults import *
from .TestResult import TestResult
from .TestConfig import TestConfig
import pyjson5 as json
from datetime import datetime

class TestResultFactory:
    TR_DICT = {
        NumericTestResult.result_type: NumericTestResult,
        BoolTestResult.result_type: BoolTestResult,
        StringTestResult.result_type: StringTestResult,
        PassFailTestResult.result_type: PassFailTestResult,
        Numeric2dTestResult.result_type: Numeric2dTestResult,
    }

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(TestResultFactory, cls).__new__(cls)
        return cls.instance

    def __init__(self) -> None:
        self.tr_dict = TestResultFactory.TR_DICT

    def add(self, result_class: TestResult):
        self.tr_dict.update({result_class.classname: result_class})

    def from_dict(self, d):
        try:
            tolerance = json.loads(d['tolerance'])
        except (json.Json5DecoderException, json.Json5Exception, TypeError, ValueError):
            tolerance = {}

        cfg = TestConfig(attr=d['attr'], tolerance=tolerance, unit=d['unit'], \
                         name=d['name'], infoonly=d['infoonly'], skip=d['skip'])
        try:
            value = self.tr_dict[d['result_type']].value_from_str(d['value'])
        except:
            value = None
        comment = d['comment']
        suite = d['suite']

        result = self.tr_dict[d['result_type']](config=cfg, value=value, comment=comment, suite=suite)
        result.result = TestResult.TestEval[d['result']]
        result.date = datetime.strptime(d['date'], '%Y-%m-%d %H:%M:%S.%f')
        return result

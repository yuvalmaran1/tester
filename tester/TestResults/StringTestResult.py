from abc import ABC, ABCMeta
from ..TestCase import TestCase
from ..TestConfig import TestConfig
from ..TestResult import TestResult

class StringTestCase(TestCase, ABC):
    __metaclass__ = ABCMeta
    
    def result_class(self):
        return StringTestResult

class StringTestResult(TestResult):
    result_type = "string"

    def _evaluate(self) -> TestResult.TestEval:
        expected = self.tolerance.get('expected', "")

        if type(self.value) is str: 
            if (self.value == expected):
                ret = TestResult.TestEval.PASS
            else:
                ret = TestResult.TestEval.FAIL
        else:
            ret = TestResult.TestEval.ERROR
        return ret
    
    def _min_str(self) -> str:
        return self.tolerance.get('expected', '')
    
    def _value_str(self) -> str:
        return self.value

    def _max_str(self) -> str:
        return self.tolerance.get('expected', '')
    
    @classmethod
    def value_from_str(cls, val: str):
        return val
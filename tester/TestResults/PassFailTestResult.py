from abc import ABC, ABCMeta
from ..TestCase import TestCase
from ..TestConfig import TestConfig
from ..TestResult import TestResult

class PassFailTestCase(TestCase, ABC):
    __metaclass__ = ABCMeta
    
    def result_class(self):
        return PassFailTestResult

class PassFailTestResult(TestResult):
    result_type = "none"

    def _evaluate(self) -> TestResult.TestEval:
        if type(self.value) == TestResult.TestEval:
            ret = self.value
        else:
            ret = TestResult.TestEval.ERROR
        return ret

    def _min_str(self) -> str:
        return ''
    
    def _value_str(self) -> str:
        return ''

    def _max_str(self) -> str:
        return ''
    
    @classmethod
    def value_from_str(cls, val: str):
        return TestResult.TestEval[val]
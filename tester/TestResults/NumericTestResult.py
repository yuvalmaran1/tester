from abc import ABC, ABCMeta
from ..TestCase import TestCase
from ..TestConfig import TestConfig
from ..TestResult import TestResult
from numbers import Number

class NumericTestCase(TestCase, ABC):
    __metaclass__ = ABCMeta
    
    def result_class(self):
        return NumericTestResult

class NumericTestResult(TestResult):
    result_type = "numeric"

    def _evaluate(self) -> TestResult.TestEval:
        tol_min = self.tolerance.get('min', 0)
        tol_max = self.tolerance.get('max', 0)

        if isinstance(self.value, Number): 
            if (self.value >= tol_min) and (self.value <= tol_max):
                ret = TestResult.TestEval.PASS
            else:
                ret = TestResult.TestEval.FAIL
        else:
            ret = TestResult.TestEval.ERROR
        return ret
    
    def _min_str(self) -> str:
        return str(self.tolerance.get('min', ''))
    
    def _value_str(self) -> str:
        return str(self.value)

    def _max_str(self) -> str:
        return str(self.tolerance.get('max', ''))
    
    @classmethod
    def value_from_str(cls, val: str):
        return float(val)
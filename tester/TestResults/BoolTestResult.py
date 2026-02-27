from abc import ABC, ABCMeta
from ..TestCase import TestCase
from ..TestConfig import TestConfig
from ..TestResult import TestResult

class BoolTestCase(TestCase, ABC):
    __metaclass__ = ABCMeta
    
    def result_class(self):
        return BoolTestResult
        
class BoolTestResult(TestResult, ABC):
    result_type = "bool"   

    def _evaluate(self) -> TestResult.TestEval:
        expected = self.tolerance.get('expected', True)

        if type(self.value) is bool: 
            if (self.value == expected):
                ret = TestResult.TestEval.PASS
            else:
                ret = TestResult.TestEval.FAIL
        else:
            ret = TestResult.TestEval.ERROR
        return ret
    
    def _min_str(self) -> str:
        return str(self.tolerance.get('expected', ''))
    
    def _value_str(self) -> str:
        return str(self.value)

    def _max_str(self) -> str:
        return str(self.tolerance.get('expected', ''))
    
    @classmethod
    def value_from_str(cls, val: str):
        return val == 'True'
    

    

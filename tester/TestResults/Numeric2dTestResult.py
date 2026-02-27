import numpy as np
import pyjson5 as json
from abc import ABC, ABCMeta
from ..TestCase import TestCase
from ..TestConfig import TestConfig
from ..TestResult import TestResult
from numbers import Number

class Numeric2dTestCase(TestCase, ABC):
    """Test case for X-Y values"""
    __metaclass__ = ABCMeta

    def result_class(self):
        return Numeric2dTestResult

class Numeric2dTestResult(TestResult):
    """Test result for X-Y values"""
    result_type = "numeric2d"

    def _evaluate(self) -> TestResult.TestEval:
        tol_min = self.tolerance.get('min', 0)
        tol_max = self.tolerance.get('max', 0)

        if isinstance(self.value, dict):
            x = self.value.get('x', None)
            y = self.value.get('y', None)

            if x is None or y is None:
                raise ValueError("value does not contain x,y vectors")

            # evaluate the tolerances in each x value via linear interpolation
            if isinstance(tol_min, dict):
                min_y = np.interp(x, tol_min['x'], tol_min['y'])
            elif isinstance(tol_min, Number):
                min_y = tol_min * np.ones(np.array(x).shape)
            else:
                raise ValueError('Invalid min tolerance')

            if isinstance(tol_max, dict):
                max_y = np.interp(x, tol_max['x'], tol_max['y'])
            elif isinstance(tol_max, Number):
                max_y = tol_max * np.ones(np.array(x).shape)
            else:
                raise ValueError('Invalid min tolerance')

            res = {"x": x, "min": min_y, "value": y, "max": max_y}

            self.plot_data = {
                "points": [dict(zip(res,t)) for t in zip(*res.values())],
                "xlabel": self.x_unit,
                "ylabel": self.unit
                }

            # check y for each point
            ret = TestResult.TestEval.PASS
            for i in range(len(x)):
                if (y[i] > max_y[i]) or (y[i] < min_y[i]):
                    ret = TestResult.TestEval.FAIL
                    break
        else:
            raise ValueError("value is not a dict")

        return ret

    def _min_str(self) -> str:
        return '-----'

    def _value_str(self) -> str:
        return '--See Plot--'

    def _max_str(self) -> str:
        return '-----'

    @classmethod
    def value_from_str(cls, val: str):
        try:
            return json.loads(val)
        except (json.Json5DecoderException, json.Json5Exception, TypeError, ValueError):
            return None

'''
Example tests
'''
import numpy as np
from tester.TestResult import TestResult
from tester.TestConfig import TestConfig
from tester.TestResults.StringTestResult import StringTestCase
from tester.TestResults.NumericTestResult import NumericTestCase
from tester.TestResults.PassFailTestResult import PassFailTestCase
from tester.TestResults.BoolTestResult import BoolTestCase
from tester.TestResults.Numeric2dTestResult import Numeric2dTestCase

class StringExampleTest(StringTestCase):
    '''
    Example string test case
    '''
    def _execute(self, config: TestConfig, assets: dict) -> str:
        return "Hello, World!"

class NumericExampleTest(NumericTestCase):
    '''
    Example numeric test case
    '''
    def _execute(self, config: TestConfig, assets: dict) -> float:
        return 1.0

class PassFailExampleTest(PassFailTestCase):
    '''
    Example pass fail test case
    '''
    def _execute(self, config: TestConfig, assets: dict) -> TestResult.TestEval:
        return TestResult.TestEval.PASS

class BoolExampleTest(BoolTestCase):
    '''
    Example bool test case
    '''
    def _execute(self, config: TestConfig, assets: dict) -> bool:
        self.set_comment("This is a test comment")
        return True

class Numeric2dExampleTest(Numeric2dTestCase):
    '''
    Example numeric 2d test case - generates a sine wave from 0 to 2π
    '''
    def _execute(self, config: TestConfig, assets: dict) -> dict:
        # Generate 100 points from 0 to 2π
        x = np.linspace(0, 2 * np.pi, 100)
        # Generate corresponding sine values
        y = np.sin(x)
        return {"x": x.tolist(), "y": y.tolist()}

class Numeric2dExampleTest2(Numeric2dTestCase):
    '''
    Example numeric 2d test case - generates a cosine wave from 0 to 2π
    '''
    def _execute(self, config: TestConfig, assets: dict) -> dict:
        # Generate 100 points from 0 to 2π
        x = np.linspace(0, 2 * np.pi, 100)
        # Generate corresponding sine values
        y = np.cos(x)
        return {"x": x.tolist(), "y": y.tolist()}

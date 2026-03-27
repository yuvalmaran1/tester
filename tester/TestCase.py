import traceback
from abc import ABC, abstractmethod, ABCMeta
from datetime import datetime
from copy import deepcopy
from .TestConfig import TestConfig
from .TestResult import TestResult
from .TestLogger import TestLogger
from .TestUtil import AbortRunException

class TestCase(ABC):
    __metaclass__ = ABCMeta
    __executing = False

    @staticmethod
    def is_executing():
        return TestCase.__executing

    def __init__(self, config: TestConfig, assets: dict, suite: str):
        super().__init__()
        self.config = config
        self.assets = assets
        self.suite = suite
        self.result = self.result_class()(self.config, None, suite=suite)
            
    def execute(self, run_data: dict):
        self.result.date = datetime.now(tz=None)
        try:
            TestCase.__executing = True
            self.result.value = self._execute(self.config, self.assets, run_data)
            self.result.evaluate()
            TestLogger().info(f'{self.config.name} value: {self.result.value}')
        except AbortRunException as e:
            self.result.result = TestResult.TestEval.ABORTED
            TestLogger().warning('Run aborted by user')
        except Exception as e:
            self.set_comment(str(e))
            self.result.result = TestResult.TestEval.ERROR
            tb_sum = traceback.extract_tb(e.__traceback__)[-1]
            trace = f"Exception on: {tb_sum.filename}, line {tb_sum.lineno}, '{tb_sum.line}'"
            TestLogger().error(f'{self.config.name} exception: {str(e)}')
            TestLogger().error(trace)
        finally:
            TestCase.__executing = False

    def skip(self):
        self.result.date = datetime.now(tz=None)
        self.result.result = TestResult.TestEval.SKIPPED
        
    def set_comment(self, comment=""):
        TestLogger().info(f"set comment: '{comment}'")
        self.result.comment = comment

    def __deepcopy__(self, memo):
        return self.__class__(deepcopy(self.config, memo), self.assets, deepcopy(self.suite, memo))

    @abstractmethod
    def _execute(self, config: TestConfig, assets, run_data: dict) -> any:
        pass

    @property
    @abstractmethod
    def result_class(self) -> TestResult:
        pass
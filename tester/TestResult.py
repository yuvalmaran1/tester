from datetime import datetime
from enum import Enum
from .TestConfig import TestConfig
from abc import ABC, abstractmethod, abstractclassmethod, ABCMeta

class TestResult(ABC):
    __metaclass__ = ABCMeta

    class TestEval(Enum):
        def __str__(self):
            return self.name
        SKIPPED = 3
        INFOONLY = 2
        UNKNOWN = 1
        PASS = 0
        FAIL = -1
        ERROR = -2
        ABORTED = -3

    def __init__(self, config: TestConfig, value: any, comment: str = "", suite: str="undefined") -> None:
        super().__init__()
        self.date: datetime = datetime.now(tz=None)
        self.name: str = config.name
        self.suite: str = suite
        self.tolerance = config.tolerance
        self.value = value
        self.comment: str = comment
        self.infoonly: bool = config.infoonly
        self.skip: bool = config.skip
        self.unit = config.unit
        self.x_unit = config.x_unit
        self.attr = config.attr
        self.plot_data = {}
        self.result: TestResult.TestEval = TestResult.TestEval.UNKNOWN
        if self.value is not None:
            self.evaluate()

    def to_dict(self) -> dict:
        return  {
            "Time": self.date,
            "Suite": self.suite,
            "Name": self.name,
            "Min": self._min_str(),
            "Value": self._value_str(),
            "Max": self._max_str(),
            "Unit": self.unit,
            "X_Unit": getattr(self, 'x_unit', ''),
            "Result": self.result.name,
            "Comment": self.comment,
            "PlotData": self.plot_data,
            "ResultType": getattr(self, 'result_type', 'unknown')
        }

    def evaluate(self) -> None:
        result = TestResult.TestEval.ERROR
        try:
            if self.skip:
                result = TestResult.TestEval.SKIPPED
            elif self.infoonly:
                result = TestResult.TestEval.INFOONLY
            else:
                result = self._evaluate()
        finally:
            self.result = result


    @abstractmethod
    def _evaluate(self) -> TestEval:
        ...

    @property
    @abstractmethod
    def result_type(self) -> str:
        ...

    @abstractmethod
    def _min_str(self) -> str:
        ...

    @abstractmethod
    def _max_str(self) -> str:
        ...

    @abstractmethod
    def _value_str(self) -> str:
        ...

    @abstractclassmethod
    def value_from_str(cls, val: str):
        ...

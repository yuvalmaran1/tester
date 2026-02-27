from typing import List
from importlib import import_module, reload
from .TestCase import TestCase
from .TestResult import TestResult
from .TestConfig import TestConfig

class TestSuite:
    def __init__(self) -> None:
        self.name = "untitled"
        self.eval: TestResult.TestEval = TestResult.TestEval.UNKNOWN
        self.testcases: List[TestCase] = []
        self.setup: TestCase = None
        self.cleanup: TestCase = None
        self.attr = {}

    def append_test(self, test: TestCase):
        self.testcases.append(test)

    @staticmethod
    def from_dict(d, assets: dict):
        s = TestSuite()
        s.name = d.get('name', s.name)
        s.attr = d.get('attr', {})

        mod = import_module(d.get('module'))
        mod = reload(mod)

        setup_name = d.get('setup', None)
        if setup_name:
            setup_test = getattr(mod, setup_name)
            setup_d = { 'name':  f"Setup" }
            setup_cfg = TestConfig.from_dict(setup_d)
            setup_cfg.attr = s.attr | setup_cfg.attr
            s.setup = setup_test(setup_cfg, assets, s.name)

        cleanup_name = d.get('cleanup', None)
        if cleanup_name:
            cleanup_test = getattr(mod, cleanup_name)
            cleanup_d = { 'name':  f"Cleanup" }
            cleanup_cfg = TestConfig.from_dict(cleanup_d)
            cleanup_cfg.attr = s.attr | cleanup_cfg.attr
            s.cleanup = cleanup_test(cleanup_cfg, assets, s.name)

        for tc_d in d.get('testcases', []):
            tc_mod = import_module(tc_d.get('module',d.get('module')))
            tc_mod = reload(tc_mod)
            tc = getattr(tc_mod, tc_d.get('test'))
            tc_cfg = TestConfig.from_dict(tc_d)
            tc_cfg.attr = s.attr | tc_cfg.attr
            s.testcases.append(tc(tc_cfg, assets, s.name))

        return s
    
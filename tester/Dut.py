import json
from typing import List
from .TestProgram import TestProgram
from .TestSuite import TestSuite
from .TestCase import TestCase
from .TestConfig import TestConfig
from importlib import import_module, reload

class Dut:
    def __init__(self) -> None:
        self.name: str = "unnamed"
        self.description: str = ""
        self.image: str = ""
        self.product_id: str = ""
        self.programs: List[TestProgram] = []
        self.test_suites: List[TestSuite] = []
        self.assets = {}
        self.attr = {}
        self.setup: TestCase = None
        self.cleanup: TestCase = None

    @staticmethod
    def from_dict(d: dict, assets: dict = {}, debug_reload: bool = False):
        dut = Dut()
        dut.name = d.get("name", dut.name)
        dut.description = d.get("description", dut.description)
        dut.image = d.get("image", "")
        dut.product_id = d.get("product_id", "")
        dut.attr = d.get("attr", {})
        dut.assets = assets

        if d.get('module', None) is not None:
            mod = import_module(d.get('module'))
            if debug_reload:
                mod = reload(mod)
            setup_name = d.get('setup', None)
            if setup_name:
                setup_test = getattr(mod, setup_name)
                setup_d = { 'name':  "Setup" }
                setup_cfg = TestConfig.from_dict(setup_d)
                setup_cfg.attr |= dut.attr
                dut.setup = setup_test(setup_cfg, assets, '')

            cleanup_name = d.get('cleanup', None)
            if cleanup_name:
                cleanup_test = getattr(mod, cleanup_name)
                cleanup_d = { 'name':  "Cleanup" }
                cleanup_cfg = TestConfig.from_dict(cleanup_d)
                cleanup_cfg.attr |= dut.attr
                dut.cleanup = cleanup_test(cleanup_cfg, assets, '')

        test_suites = d.get("testsuites", [])
        for t in test_suites:
            ts_path = t.get('path', None)
            if ts_path:
                fp = open(ts_path,'r')
                ts_obj = json.load(fp)
                fp.close()
            else:
                ts_obj = t
            ts_obj['attr'] = ts_obj.get('attr',{}) | dut.attr
            ts = TestSuite.from_dict(ts_obj, assets, debug_reload=debug_reload)
            dut.test_suites.append(ts)

        programs = d.get("programs", [])
        for p in programs:
            prog = TestProgram.from_dict(p, dut.test_suites, assets=assets, debug_reload=debug_reload)
            dut.programs.append(prog)
        return dut
        
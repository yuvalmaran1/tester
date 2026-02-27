from dataclasses import dataclass, field

@dataclass
class TestConfig:
    attr: dict
    tolerance: dict
    unit: str = ''
    x_unit: str = ''
    name: str = field(default="untitled")
    abortonfailure: bool = field(default=False)
    infoonly: bool = field(default=False)
    skip: bool = field(default=False)

    @staticmethod
    def from_dict(d):
        tc = TestConfig(attr={}, tolerance={})
        tc.name = d.get("name", tc.name)
        tc.unit = d.get("unit", tc.unit)
        tc.x_unit = d.get("x_unit", tc.x_unit)
        tc.tolerance = d.get("tolerance", tc.tolerance)
        tc.abortonfailure = d.get("abortonfailure", tc.abortonfailure)
        tc.infoonly = d.get("infoonly", tc.infoonly)
        tc.skip = d.get("skip", tc.skip)
        tc.attr = d.get("attr", tc.attr)
        return tc

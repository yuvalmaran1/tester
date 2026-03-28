"""
sn_generators.py
================
Example serial-number generators for the Smart Sensor Board example tester.

Each generator is a StringTestCase subclass declared in duts.json under the
program's ``sn_generator`` key::

    "sn_generator": {
        "module": "sn_generators",
        "test": "IncrementalSNGenerator"
    }

The framework executes the test case before each run and uses the returned
string as the serial number. The manual serial-number input in the UI is
hidden when a generator is active.
"""
import time

from tester.TestResults.StringTestResult import StringTestCase
from tester.TestConfig import TestConfig


class IncrementalSNGenerator(StringTestCase):
    """Generates sequential serial numbers: SSB-<YYYYMMDD>-<NNNN>.

    The counter is maintained across runs for the lifetime of the loaded DUT.
    In a real factory integration this would read from and write to a shared
    counter stored in a database or file.
    """

    def __init__(self, config: TestConfig, assets: dict, suite: str):
        super().__init__(config, assets, suite)
        self._counter = 0

    def _execute(self, config: TestConfig, assets: dict, run_data: dict) -> str:
        self._counter += 1
        date_str = time.strftime("%Y%m%d")
        return f"SSB-{date_str}-{self._counter:04d}"

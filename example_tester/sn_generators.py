"""
sn_generators.py
================
Example serial-number generators for the Smart Sensor Board example tester.

Demonstrates how to subclass SNGenerator and declare it in duts.json under
a program's ``sn_generator`` key.
"""
import time

from tester import SNGenerator


class IncrementalSNGenerator(SNGenerator):
    """Generates sequential serial numbers: SSB-<YYYYMMDD>-<NNNN>.

    The counter resets to 1 each time a new instance is created (i.e. on
    every DUT reload).  In a real factory integration this would read from
    and write to a shared counter stored in a database or file.
    """

    def __init__(self, assets):
        super().__init__(assets)
        self._counter = 0

    def generate(self) -> str:
        self._counter += 1
        date_str = time.strftime("%Y%m%d")
        return f"SSB-{date_str}-{self._counter:04d}"

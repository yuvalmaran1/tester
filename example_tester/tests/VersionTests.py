'''
Node version related test cases
'''
from time import sleep
from typing import cast
from tester.TestResults.StringTestResult import StringTestCase
from tester.TestConfig import TestConfig

class NodeVersionsTest(StringTestCase):
    '''
    Validates node versions via debug interface
    '''
    def _execute(self, config: TestConfig, assets: dict) -> str:
        ver_type = config.attr.get("ver_type", None)
        comment = config.attr.get("comment", None)

        if comment:
            self.set_comment(comment)

        sleep(1)

        if ver_type == "fw":
            return f"1.1.1.1"
        elif ver_type == "hw":
            return f"1"
        else:
            raise ValueError(f'Invalid version type {ver_type}')

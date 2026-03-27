'''
Generic tests for all test suits
'''
from time import sleep
from typing import cast
from tester.TestResult import TestResult
from tester.TestConfig import TestConfig
from tester.TestResults.PassFailTestResult import PassFailTestCase
from tester.TestLogger import TestLogger

class DutSetupTest(PassFailTestCase):
    '''
    DUT setup test - performed prior to test suites
    '''
    def _execute(self, config: TestConfig, assets, run_data: dict) -> TestResult.TestEval:

        TestLogger().debug('setting dut voltage')

        TestLogger().debug('powering off dut')

        TestLogger().debug('powering on dut')

        sleep(1)

        return TestResult.TestEval.PASS

class DutCleanupTest(PassFailTestCase):
    '''
    DUT cleanup test - performed prior to completion
    '''
    def _execute(self, config: TestConfig, assets, run_data: dict) -> TestResult.TestEval:

        sleep(1)

        return TestResult.TestEval.PASS

class SetupTest(PassFailTestCase):
    '''
    setup test - performed prior to test suite
    '''
    def _execute(self, config: TestConfig, assets, run_data: dict) -> TestResult.TestEval:

        sleep(1)

        return TestResult.TestEval.PASS

class CleanupTest(PassFailTestCase):
    '''
    cleanup test - performed after test suite
    '''
    def _execute(self, config: TestConfig, assets, run_data: dict) -> TestResult.TestEval:

        sleep(1)

        return TestResult.TestEval.PASS

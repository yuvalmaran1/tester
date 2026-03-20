import copy
from typing import List
from .TestResult import TestResult
from .TestCase import TestCase
from .TestSuite import TestSuite

class TestProgram:
    def __init__(self) -> None:
        self.name = "untitled"
        self.description = ""
        self.eval: TestResult.TestEval = TestResult.TestEval.UNKNOWN
        self.testsuites: List[TestSuite] = []
        self.attr = {}
        self.attr_schema = {}

    @staticmethod
    def from_dict(d, test_suits: List[TestSuite]):
        p = TestProgram()
        p.name = d.get('name', p.name)
        p.description = d.get('description', p.description)
        p.attr = d.get('attr', {})
        p.attr_schema = d.get('attr_schema', {"type": "object", "properties": {}})

        for ts_item in d.get('testsuites', []):
            # Support both string format (backwards compatible) and object format (new)
            if isinstance(ts_item, str):
                # Backwards compatible: just the testsuite name
                ts_name = ts_item
                ts_attr = {}
                custom_name = None
            else:
                # Object format: support both old and new formats
                # Old format: 'name' for testsuite selection
                # New format: 'testsuite' for selection, 'name' for custom display
                if 'testsuite' in ts_item:
                    # New format
                    ts_name = ts_item.get('testsuite')
                    custom_name = ts_item.get('name')  # Optional custom display name
                else:
                    # Old format (backwards compatible)
                    ts_name = ts_item.get('name')
                    custom_name = None
                ts_attr = ts_item.get('attr', {})

            ts_names = [t for t in test_suits if t.name == ts_name]
            if len(ts_names) == 0:
                raise ValueError(f"Test suite {ts_name} not found")

            # Get the number of repetitions (default to 1 if not specified)
            reps = ts_item.get('reps', 1) if isinstance(ts_item, dict) else 1

            # Create a testsuite for each repetition
            for rep_num in range(1, reps + 1):
                ts = copy.deepcopy(next(iter(ts_names)))

                # Determine the final testsuite name
                if custom_name:
                    if reps > 1:
                        # Append rep number to custom name if there are multiple reps
                        final_name = f"{custom_name} Rep#{rep_num}"
                    else:
                        final_name = custom_name
                else:
                    if reps > 1:
                        # Append rep number to original testsuite name
                        final_name = f"{ts.name} Rep#{rep_num}"
                    else:
                        final_name = ts.name

                # Set the testsuite name
                ts.name = final_name
                # Update all test case results to use the final suite name
                if ts.setup:
                    ts.setup.suite = final_name
                    ts.setup.result.suite = final_name
                if ts.cleanup:
                    ts.cleanup.suite = final_name
                    ts.cleanup.result.suite = final_name
                for tc in ts.testcases:
                    tc.suite = final_name
                    tc.result.suite = final_name

                # Merge program attr, testsuite attr, and new ts_attr
                # Most specific wins (rightmost in |): ts_attr > ts.attr > p.attr
                ts.attr = p.attr | ts.attr | ts_attr

                if ts.setup:
                    # Program context wins: ts_attr > p.attr > ts.attr > setup defaults
                    ts.setup.config.attr = ts.setup.config.attr | ts.attr | p.attr | ts_attr

                if ts.cleanup:
                    # Program context wins: ts_attr > p.attr > ts.attr > cleanup defaults
                    ts.cleanup.config.attr = ts.cleanup.config.attr | ts.attr | p.attr | ts_attr

                for tc in ts.testcases:
                    # Program context wins: ts_attr > p.attr > ts.attr > testcase defaults
                    tc.config.attr = tc.config.attr | ts.attr | p.attr | ts_attr
                p.testsuites.append(ts)
        return p

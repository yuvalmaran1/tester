"""Shared pytest fixtures for the tester backend test suite.

Puts ``tests/`` on sys.path so that ``fixtures.fast_tests`` is importable
by the duts.json data that is written into tmp_path for each integration test.
"""
import sys
import json
import uuid
import pytest
from pathlib import Path

# Allow "fixtures.fast_tests" to be imported by test code and duts.json refs.
sys.path.insert(0, str(Path(__file__).parent))

from tester import Tester
from tester.TesterConfig import TesterConfig
from tester.TestLogger import TestLogger


# ---------------------------------------------------------------------------
# Session-level: initialise the TestLogger singleton once so that every
# TestCase.execute() call inside tests has a valid logger.
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def init_logger():
    """Bootstrap the TestLogger singleton with no file output."""
    TestLogger(name="test", dirname=None)


# ---------------------------------------------------------------------------
# Minimal concrete Tester subclass (no real hardware)
# ---------------------------------------------------------------------------

class MinimalTester(Tester):
    """Headless Tester subclass used by all integration tests."""
    def _init(self, station_config) -> dict:
        return {}


# ---------------------------------------------------------------------------
# Canonical duts.json data sets
# ---------------------------------------------------------------------------

#: Standard configuration: DUT setup/cleanup pass, one suite with a
#: passing test and a failing test.
DUTS_STANDARD = {
    "duts": [{
        "name": "Test DUT",
        "description": "DUT for testing",
        "image": "",
        "product_id": "test-001",
        "module": "fixtures.fast_tests",
        "setup": "FastSetupTest",
        "cleanup": "FastCleanupTest",
        "attr": {"dut_key": "dut_value", "read_key": "from_dut"},
        "programs": [{
            "name": "Test Program",
            "description": "Test program",
            "attr": {"prog_key": "prog_value", "read_key": "from_program"},
            "testsuites": ["Suite1"]
        }],
        "testsuites": [{
            "name": "Suite1",
            "module": "fixtures.fast_tests",
            "setup": "FastSetupTest",
            "cleanup": "FastCleanupTest",
            "testcases": [
                {
                    "name": "Pass Test",
                    "module": "fixtures.fast_tests",
                    "test": "FastPassTest",
                    "tolerance": {}
                },
                {
                    "name": "Fail Test",
                    "module": "fixtures.fast_tests",
                    "test": "FastFailTest",
                    "tolerance": {}
                }
            ]
        }]
    }]
}

#: Configuration where the DUT-level setup always fails, causing all test
#: suites to be skipped.
DUTS_DUT_SETUP_FAIL = {
    "duts": [{
        "name": "Test DUT",
        "description": "DUT with failing setup",
        "image": "",
        "product_id": "test-002",
        "module": "fixtures.fast_tests",
        "setup": "FastSetupFailTest",
        "cleanup": "FastCleanupTest",
        "attr": {},
        "programs": [{
            "name": "Test Program",
            "description": "Test program",
            "attr": {},
            "testsuites": ["Suite1"]
        }],
        "testsuites": [{
            "name": "Suite1",
            "module": "fixtures.fast_tests",
            "testcases": [
                {
                    "name": "Pass Test",
                    "module": "fixtures.fast_tests",
                    "test": "FastPassTest",
                    "tolerance": {}
                }
            ]
        }]
    }]
}

#: Configuration with a slow test that can be aborted mid-run.
DUTS_SLOW = {
    "duts": [{
        "name": "Test DUT",
        "description": "DUT with slow test",
        "image": "",
        "product_id": "test-003",
        "attr": {},
        "programs": [{
            "name": "Test Program",
            "description": "Test program",
            "attr": {},
            "testsuites": ["SlowSuite"]
        }],
        "testsuites": [{
            "name": "SlowSuite",
            "module": "fixtures.fast_tests",
            "testcases": [
                {
                    "name": "Slow Test",
                    "module": "fixtures.fast_tests",
                    "test": "SlowTest",
                    "tolerance": {}
                },
                {
                    "name": "After Slow",
                    "module": "fixtures.fast_tests",
                    "test": "FastPassTest",
                    "tolerance": {}
                }
            ]
        }]
    }]
}

#: Configuration with AttrReadTest so attr-hierarchy tests can inspect the
#: value that flows through the merge chain at runtime.
DUTS_ATTR_READ = {
    "duts": [{
        "name": "Test DUT",
        "description": "DUT for attr hierarchy testing",
        "image": "",
        "product_id": "test-004",
        "attr": {"read_key": "from_dut"},
        "programs": [{
            "name": "Test Program",
            "description": "Test program",
            "attr": {"read_key": "from_program"},
            "testsuites": ["AttrSuite"]
        }],
        "testsuites": [{
            "name": "AttrSuite",
            "module": "fixtures.fast_tests",
            "testcases": [{
                "name": "Attr Test",
                "module": "fixtures.fast_tests",
                "test": "AttrReadTest",
                "tolerance": {"expected": "from_program"}
            }]
        }]
    }]
}

#: Two-test suite where TC1 writes to run_data and TC2 reads it back.
#: Verifies that run_data flows between consecutive test cases in a run.
DUTS_RUN_DATA = {
    "duts": [{
        "name": "Test DUT",
        "description": "DUT for run_data testing",
        "image": "",
        "product_id": "test-005",
        "attr": {},
        "programs": [{
            "name": "Test Program",
            "description": "Test program",
            "attr": {},
            "testsuites": ["RunDataSuite"]
        }],
        "testsuites": [{
            "name": "RunDataSuite",
            "module": "fixtures.fast_tests",
            "testcases": [
                {
                    "name": "Write Test",
                    "module": "fixtures.fast_tests",
                    "test": "RunDataWriteTest",
                    "tolerance": {}
                },
                {
                    "name": "Read Test",
                    "module": "fixtures.fast_tests",
                    "test": "RunDataReadTest",
                    "tolerance": {"expected": "hello"}
                }
            ]
        }]
    }]
}

STATION_DATA = {"serial_port": "COM1", "ip_address": "127.0.0.1"}

#: Program with an SN generator; the generator produces sequential SN-NNNN values.
DUTS_SN_GENERATOR = {
    "duts": [{
        "name": "Test DUT",
        "description": "DUT for SN generator testing",
        "image": "",
        "product_id": "test-006",
        "attr": {},
        "programs": [{
            "name": "Test Program",
            "description": "Test program with SN generator",
            "sn_generator": {
                "module": "fixtures.fast_tests",
                "test": "SequentialSNGenerator"
            },
            "testsuites": ["Suite1"]
        }],
        "testsuites": [{
            "name": "Suite1",
            "module": "fixtures.fast_tests",
            "testcases": [{
                "name": "Pass Test",
                "module": "fixtures.fast_tests",
                "test": "FastPassTest",
                "tolerance": {}
            }]
        }]
    }]
}


# ---------------------------------------------------------------------------
# Factory fixture: build a MinimalTester from arbitrary duts data
# ---------------------------------------------------------------------------

@pytest.fixture
def make_tester(tmp_path):
    """Factory fixture: ``make_tester(duts_data=None)`` → ``MinimalTester``.

    Uses a unique subdirectory per call so multiple testers can be created
    within one test without file-path collisions.  All created testers are
    joined on teardown.
    """
    created = []

    def _factory(duts_data=None):
        if duts_data is None:
            duts_data = DUTS_STANDARD
        subdir = tmp_path / str(uuid.uuid4())
        subdir.mkdir()
        (subdir / "duts.json").write_text(json.dumps(duts_data))
        (subdir / "station.json").write_text(json.dumps(STATION_DATA))
        cfg = TesterConfig(
            name="Test Tester",
            description="Testing",
            version="0.0.1",
            db_config=str(subdir / "test.db"),
            station_config_file=str(subdir / "station.json"),
            duts_file=str(subdir / "duts.json"),
            log_dir=None,
            ui=False,
        )
        t = MinimalTester(cfg)
        created.append(t)
        return t

    yield _factory

    for t in created:
        t.wait_for_test_end()


# ---------------------------------------------------------------------------
# Convenience: pre-built headless tester using DUTS_STANDARD
# ---------------------------------------------------------------------------

@pytest.fixture
def headless_tester(make_tester):
    """Ready-to-use MinimalTester with the standard DUT configuration."""
    return make_tester(DUTS_STANDARD)

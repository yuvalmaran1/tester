"""Unit tests for TestRun: construction, result aggregation, start/end lifecycle."""
from datetime import datetime
from tester.TestRun import TestRun
from tester.TestResult import TestResult
from tester.TestConfig import TestConfig
from tester.TestResults.PassFailTestResult import PassFailTestResult

E = TestResult.TestEval


def _make_run(dut='DUT', program='Prog'):
    return TestRun(
        tester={'name': 'T', 'version': '1.0'},
        dut={'name': dut, 'description': 'desc', 'product_id': 'p1', 'image': ''},
        program={'name': program, 'description': 'pdesc', 'attr': {'k': 'v'}},
    )


def _make_result(eval_val, suite='S', name='t'):
    cfg = TestConfig(attr={}, tolerance={}, name=name)
    return PassFailTestResult(cfg, eval_val, suite=suite)


# ── Construction ─────────────────────────────────────────────────────────────

def test_initial_fields():
    run = _make_run()
    assert run.dut == 'DUT'
    assert run.program == 'Prog'
    assert run.tester == 'T'
    assert run.tester_ver == '1.0'
    assert run.program_attr == {'k': 'v'}
    assert run.result == E.UNKNOWN
    assert run.start_date is None
    assert run.end_date is None
    assert run.program_modified is False
    assert run.test_results == []


def test_append_result():
    run = _make_run()
    r = _make_result(E.PASS)
    run.append_result(r)
    assert len(run.test_results) == 1
    assert run.test_results[0] is r


# ── Lifecycle ────────────────────────────────────────────────────────────────

def test_start_sets_start_date():
    run = _make_run()
    assert run.start_date is None
    run.start()
    assert isinstance(run.start_date, datetime)


def test_end_sets_end_date():
    run = _make_run()
    run.start()
    run.append_result(_make_result(E.PASS))
    run.end()
    assert isinstance(run.end_date, datetime)


def test_end_triggers_evaluate():
    run = _make_run()
    run.start()
    run.append_result(_make_result(E.FAIL))
    run.end()
    assert run.result == E.FAIL


# ── Result aggregation ───────────────────────────────────────────────────────

def test_aggregate_all_pass():
    run = _make_run()
    for _ in range(3):
        run.append_result(_make_result(E.PASS))
    run.evaluate()
    assert run.result == E.PASS


def test_aggregate_one_fail():
    run = _make_run()
    run.append_result(_make_result(E.PASS))
    run.append_result(_make_result(E.FAIL))
    run.evaluate()
    assert run.result == E.FAIL


def test_aggregate_fail_takes_priority_over_error():
    run = _make_run()
    run.append_result(_make_result(E.ERROR))
    run.append_result(_make_result(E.FAIL))
    run.evaluate()
    assert run.result == E.FAIL


def test_aggregate_error_only():
    run = _make_run()
    run.append_result(_make_result(E.ERROR))
    run.evaluate()
    assert run.result == E.ERROR


def test_aggregate_aborted_beats_fail():
    run = _make_run()
    run.append_result(_make_result(E.PASS))
    run.append_result(_make_result(E.FAIL))
    run.append_result(_make_result(E.ABORTED))
    run.evaluate()
    assert run.result == E.ABORTED


def test_aggregate_all_skipped_gives_unknown():
    """When every result is SKIPPED the run has no meaningful outcome → UNKNOWN."""
    run = _make_run()
    cfg = TestConfig(attr={}, tolerance={}, name='t', skip=True)
    for _ in range(2):
        run.append_result(PassFailTestResult(cfg, None, suite='S'))
    run.evaluate()
    assert run.result == E.UNKNOWN


def test_aggregate_empty_run_unknown():
    run = _make_run()
    run.evaluate()
    assert run.result == E.UNKNOWN


# ── from_dict round-trip ─────────────────────────────────────────────────────

def test_from_dict_reconstructs_fields():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    d = {
        'tester': 'T', 'tester_ver': '1.0',
        'dut': 'MyDUT', 'dut_desc': 'dd', 'dut_product_id': 'p1', 'dut_image': '',
        'program': 'MyProg', 'program_desc': 'pd', 'program_attr': {'x': 1},
        'start_date': now_str, 'end_date': now_str,
        'result': 'PASS',
        'log': ['line1'],
        'attachment': None,
    }
    run = TestRun.from_dict(d, [])
    assert run.dut == 'MyDUT'
    assert run.program == 'MyProg'
    assert run.program_attr == {'x': 1}
    assert run.result == E.PASS
    assert run.log == ['line1']


# ── Traceability fields ───────────────────────────────────────────────────────

def test_serial_number_default_empty():
    run = _make_run()
    assert run.serial_number == ''

def test_config_hash_default_empty():
    run = _make_run()
    assert run.config_hash == ''

def test_from_dict_preserves_serial_number():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    d = {
        'tester': 'T', 'tester_ver': '1.0',
        'dut': 'D', 'dut_desc': '', 'dut_product_id': '', 'dut_image': '',
        'program': 'P', 'program_desc': '', 'program_attr': {},
        'start_date': now_str, 'end_date': now_str,
        'result': 'PASS', 'log': [], 'attachment': None,
        'serial_number': 'SN-2026-00042',
    }
    run = TestRun.from_dict(d, [])
    assert run.serial_number == 'SN-2026-00042'

def test_from_dict_preserves_config_hash():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    d = {
        'tester': 'T', 'tester_ver': '1.0',
        'dut': 'D', 'dut_desc': '', 'dut_product_id': '', 'dut_image': '',
        'program': 'P', 'program_desc': '', 'program_attr': {},
        'start_date': now_str, 'end_date': now_str,
        'result': 'PASS', 'log': [], 'attachment': None,
        'config_hash': 'abc123',
    }
    run = TestRun.from_dict(d, [])
    assert run.config_hash == 'abc123'

def test_from_dict_missing_traceability_fields_default_empty():
    """Older DB records without serial_number/config_hash deserialise safely."""
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    d = {
        'tester': 'T', 'tester_ver': '1.0',
        'dut': 'D', 'dut_desc': '', 'dut_product_id': '', 'dut_image': '',
        'program': 'P', 'program_desc': '', 'program_attr': {},
        'start_date': now_str, 'end_date': now_str,
        'result': 'PASS', 'log': [], 'attachment': None,
    }
    run = TestRun.from_dict(d, [])
    assert run.serial_number == ''
    assert run.config_hash == ''

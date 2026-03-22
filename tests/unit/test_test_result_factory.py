"""Unit tests for TestResultFactory: singleton, built-in registrations, from_dict."""
import pytest
from tester.TestResultFactory import TestResultFactory
from tester.TestConfig import TestConfig
from tester.TestResult import TestResult
from tester.TestResults.NumericTestResult import NumericTestResult
from tester.TestResults.StringTestResult import StringTestResult
from tester.TestResults.BoolTestResult import BoolTestResult
from tester.TestResults.PassFailTestResult import PassFailTestResult
from tester.TestResults.Numeric2dTestResult import Numeric2dTestResult

E = TestResult.TestEval


def _result_dict(result_type, *, name='t', suite='S', tolerance='{}',
                 value='0', unit='', result='PASS', comment='',
                 infoonly=False, skip=False, attr='{}'):
    return {
        'result_type': result_type,
        'name': name,
        'suite': suite,
        'tolerance': tolerance,
        'value': value,
        'unit': unit,
        'result': result,
        'comment': comment,
        'infoonly': infoonly,
        'skip': skip,
        'attr': attr,
        'date': '2024-01-01 00:00:00.000000',
    }


# ── Singleton ─────────────────────────────────────────────────────────────────

def test_factory_is_singleton():
    assert TestResultFactory() is TestResultFactory()


# ── Built-in registrations ────────────────────────────────────────────────────

def test_builtin_numeric_registered():
    assert 'numeric' in TestResultFactory().tr_dict


def test_builtin_string_registered():
    assert 'string' in TestResultFactory().tr_dict


def test_builtin_bool_registered():
    assert 'bool' in TestResultFactory().tr_dict


def test_builtin_passfail_registered():
    assert 'none' in TestResultFactory().tr_dict   # PassFailTestResult.result_type == "none"


def test_builtin_numeric2d_registered():
    assert 'numeric2d' in TestResultFactory().tr_dict


# ── from_dict reconstruction ──────────────────────────────────────────────────

def test_from_dict_numeric():
    d = _result_dict('numeric', tolerance='{"min": 0, "max": 2}', value='1.5')
    r = TestResultFactory().from_dict(d)
    assert isinstance(r, NumericTestResult)
    assert r.value == pytest.approx(1.5)


def test_from_dict_string():
    d = _result_dict('string', tolerance='{"expected": "hello"}', value='hello')
    r = TestResultFactory().from_dict(d)
    assert isinstance(r, StringTestResult)
    assert r.value == 'hello'


def test_from_dict_bool_true():
    d = _result_dict('bool', tolerance='{"expected": true}', value='True')
    r = TestResultFactory().from_dict(d)
    assert isinstance(r, BoolTestResult)
    assert r.value is True


def test_from_dict_bool_false():
    d = _result_dict('bool', tolerance='{"expected": false}', value='False')
    r = TestResultFactory().from_dict(d)
    assert r.value is False


def test_from_dict_stored_result_overrides_evaluation():
    """from_dict must restore the *stored* result, not re-evaluate from value."""
    # value=1.5 in range [0,2] → evaluated PASS, but stored result is FAIL
    d = _result_dict('numeric', tolerance='{"min": 0, "max": 2}', value='1.5', result='FAIL')
    r = TestResultFactory().from_dict(d)
    assert r.result == E.FAIL


def test_from_dict_suite_and_name():
    d = _result_dict('numeric', name='MyTest', suite='MySuite',
                     tolerance='{"min": 0, "max": 1}', value='0.5')
    r = TestResultFactory().from_dict(d)
    assert r.name == 'MyTest'
    assert r.suite == 'MySuite'


def test_from_dict_comment_preserved():
    d = _result_dict('string', tolerance='{"expected": "x"}', value='x',
                     comment='some note')
    r = TestResultFactory().from_dict(d)
    assert r.comment == 'some note'


# ── add() custom type ─────────────────────────────────────────────────────────

def test_add_registers_custom_type():
    class CustomResult(NumericTestResult):
        result_type = "_test_custom_type"

    f = TestResultFactory()
    f.add(CustomResult)
    try:
        assert '_test_custom_type' in f.tr_dict
        assert f.tr_dict['_test_custom_type'] is CustomResult
    finally:
        del f.tr_dict['_test_custom_type']   # clean up

"""Unit tests for all five TestResult subtype evaluation rules.

Each test exercises _evaluate() in isolation — no test cases, no suites,
no database.  Creates result objects directly via their constructors.
"""
import pytest
from tester.TestConfig import TestConfig
from tester.TestResult import TestResult
from tester.TestResults.NumericTestResult import NumericTestResult
from tester.TestResults.StringTestResult import StringTestResult
from tester.TestResults.BoolTestResult import BoolTestResult
from tester.TestResults.PassFailTestResult import PassFailTestResult
from tester.TestResults.Numeric2dTestResult import Numeric2dTestResult

E = TestResult.TestEval


def cfg(tolerance, *, infoonly=False, skip=False, unit='', x_unit=''):
    return TestConfig(
        attr={}, tolerance=tolerance,
        unit=unit, x_unit=x_unit,
        infoonly=infoonly, skip=skip,
    )


# ── NumericTestResult ────────────────────────────────────────────────────────

def test_numeric_pass_within_range():
    assert NumericTestResult(cfg({'min': 0.0, 'max': 2.0}), 1.0).result == E.PASS


def test_numeric_pass_at_min_boundary():
    assert NumericTestResult(cfg({'min': 1.0, 'max': 2.0}), 1.0).result == E.PASS


def test_numeric_pass_at_max_boundary():
    assert NumericTestResult(cfg({'min': 1.0, 'max': 2.0}), 2.0).result == E.PASS


def test_numeric_fail_below_min():
    assert NumericTestResult(cfg({'min': 1.0, 'max': 2.0}), 0.5).result == E.FAIL


def test_numeric_fail_above_max():
    assert NumericTestResult(cfg({'min': 0.0, 'max': 1.0}), 1.5).result == E.FAIL


def test_numeric_error_on_non_number():
    assert NumericTestResult(cfg({'min': 0.0, 'max': 2.0}), "hello").result == E.ERROR


def test_numeric_result_type():
    assert NumericTestResult.result_type == "numeric"


# ── StringTestResult ─────────────────────────────────────────────────────────

def test_string_pass_exact_match():
    assert StringTestResult(cfg({'expected': 'hello'}), 'hello').result == E.PASS


def test_string_fail_mismatch():
    assert StringTestResult(cfg({'expected': 'hello'}), 'world').result == E.FAIL


def test_string_fail_case_sensitive():
    assert StringTestResult(cfg({'expected': 'Hello'}), 'hello').result == E.FAIL


def test_string_error_on_non_string():
    assert StringTestResult(cfg({'expected': 'hello'}), 123).result == E.ERROR


def test_string_result_type():
    assert StringTestResult.result_type == "string"


# ── BoolTestResult ───────────────────────────────────────────────────────────

def test_bool_pass_true_expected_true():
    assert BoolTestResult(cfg({'expected': True}), True).result == E.PASS


def test_bool_pass_false_expected_false():
    assert BoolTestResult(cfg({'expected': False}), False).result == E.PASS


def test_bool_fail_true_expected_false():
    assert BoolTestResult(cfg({'expected': False}), True).result == E.FAIL


def test_bool_fail_false_expected_true():
    assert BoolTestResult(cfg({'expected': True}), False).result == E.FAIL


def test_bool_error_on_string_value():
    # "True" as a string is not a bool
    assert BoolTestResult(cfg({'expected': True}), "True").result == E.ERROR


def test_bool_result_type():
    assert BoolTestResult.result_type == "bool"


# ── PassFailTestResult ───────────────────────────────────────────────────────

def test_passfail_pass():
    assert PassFailTestResult(cfg({}), E.PASS).result == E.PASS


def test_passfail_fail():
    assert PassFailTestResult(cfg({}), E.FAIL).result == E.FAIL


def test_passfail_error_on_non_eval():
    assert PassFailTestResult(cfg({}), "not_an_eval").result == E.ERROR


def test_passfail_result_type():
    assert PassFailTestResult.result_type == "none"


# ── Numeric2dTestResult ──────────────────────────────────────────────────────

def test_numeric2d_pass_all_in_range():
    value = {'x': [0.0, 1.0, 2.0], 'y': [0.0, 0.5, -0.5]}
    r = Numeric2dTestResult(cfg({'min': -1.0, 'max': 1.0}, unit='V', x_unit='s'), value)
    assert r.result == E.PASS


def test_numeric2d_fail_one_out_of_range():
    value = {'x': [0.0, 1.0], 'y': [0.0, 2.0]}  # y[1]=2.0 > max=0.1
    r = Numeric2dTestResult(cfg({'min': -0.1, 'max': 0.1}), value)
    assert r.result == E.FAIL


def test_numeric2d_raises_on_missing_y():
    with pytest.raises(Exception):
        Numeric2dTestResult(cfg({'min': -1.0, 'max': 1.0}), {'x': [1.0]})


def test_numeric2d_raises_on_non_dict():
    with pytest.raises(Exception):
        Numeric2dTestResult(cfg({'min': -1.0, 'max': 1.0}), "not a dict")


def test_numeric2d_result_type():
    assert Numeric2dTestResult.result_type == "numeric2d"


def test_numeric2d_populates_plot_data():
    value = {'x': [0.0, 1.0], 'y': [0.0, 0.5]}
    r = Numeric2dTestResult(cfg({'min': -1.0, 'max': 1.0}), value)
    assert 'points' in r.plot_data


# ── Common TestResult behaviours ─────────────────────────────────────────────

def test_infoonly_overrides_fail():
    # Value 99.0 would be FAIL for min=0/max=1, but infoonly=True → INFOONLY
    r = NumericTestResult(cfg({'min': 0.0, 'max': 1.0}, infoonly=True), 99.0)
    assert r.result == E.INFOONLY


def test_skip_flag_overrides_pass():
    r = StringTestResult(cfg({'expected': 'hello'}, skip=True), 'hello')
    assert r.result == E.SKIPPED


def test_role_default_is_testcase():
    r = PassFailTestResult(cfg({}), E.PASS)
    assert r.role == "testcase"


def test_to_dict_has_required_keys():
    r = NumericTestResult(cfg({'min': 0.0, 'max': 1.0}), 0.5)
    d = r.to_dict()
    for key in ('Time', 'Suite', 'Name', 'Min', 'Value', 'Max', 'Unit', 'Result', 'Comment', 'ResultType'):
        assert key in d, f"Missing key: {key}"


def test_value_from_str_numeric():
    assert NumericTestResult.value_from_str("3.14") == pytest.approx(3.14)


def test_value_from_str_string():
    assert StringTestResult.value_from_str("hello") == "hello"


def test_value_from_str_bool_true():
    assert BoolTestResult.value_from_str("True") is True


def test_value_from_str_bool_false():
    assert BoolTestResult.value_from_str("False") is False


def test_value_from_str_passfail():
    assert PassFailTestResult.value_from_str("PASS") == E.PASS

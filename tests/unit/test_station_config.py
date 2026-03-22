"""Unit tests for StationConfig Pydantic base class and subclassing."""
import pytest
from pydantic import ValidationError
from tester.StationConfig import StationConfig


class SampleConfig(StationConfig):
    serial_port: str = "COM1"
    ip_address: str = "127.0.0.1"
    timeout: float = 5.0
    retries: int = 3


# ── Base class ───────────────────────────────────────────────────────────────

def test_base_validates_empty_dict():
    sc = StationConfig.model_validate({})
    assert sc is not None


def test_base_extra_fields_ignored():
    sc = StationConfig.model_validate({'unknown_field': 'ignored'})
    assert not hasattr(sc, 'unknown_field')


# ── Subclass defaults ────────────────────────────────────────────────────────

def test_subclass_all_defaults():
    sc = SampleConfig.model_validate({})
    assert sc.serial_port == "COM1"
    assert sc.ip_address == "127.0.0.1"
    assert sc.timeout == 5.0
    assert sc.retries == 3


def test_subclass_override_string_field():
    sc = SampleConfig.model_validate({'serial_port': 'COM3'})
    assert sc.serial_port == 'COM3'
    assert sc.ip_address == "127.0.0.1"   # unchanged


def test_subclass_override_float_field():
    sc = SampleConfig.model_validate({'timeout': 10.5})
    assert sc.timeout == 10.5


def test_subclass_override_int_field():
    sc = SampleConfig.model_validate({'retries': 5})
    assert sc.retries == 5


def test_subclass_override_multiple_fields():
    sc = SampleConfig.model_validate({'serial_port': 'COM9', 'ip_address': '10.0.0.1'})
    assert sc.serial_port == 'COM9'
    assert sc.ip_address == '10.0.0.1'
    assert sc.timeout == 5.0     # default unchanged


# ── Extra / unknown fields ignored ──────────────────────────────────────────

def test_subclass_extra_fields_ignored():
    sc = SampleConfig.model_validate({'serial_port': 'COM2', 'mystery': True})
    assert sc.serial_port == 'COM2'
    assert not hasattr(sc, 'mystery')


# ── Type validation ──────────────────────────────────────────────────────────

def test_type_error_raises_validation_error():
    with pytest.raises(ValidationError):
        SampleConfig.model_validate({'timeout': 'not_a_number'})


def test_type_error_int_field():
    with pytest.raises(ValidationError):
        SampleConfig.model_validate({'retries': 'many'})


# ── Field access ─────────────────────────────────────────────────────────────

def test_attribute_access():
    sc = SampleConfig.model_validate({'serial_port': 'COM7'})
    assert sc.serial_port == 'COM7'

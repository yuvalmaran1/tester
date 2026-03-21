"""Unit tests for TestConfig.from_dict."""
from tester.TestConfig import TestConfig


def test_defaults_when_dict_empty():
    cfg = TestConfig.from_dict({})
    assert cfg.name == "untitled"
    assert cfg.unit == ''
    assert cfg.x_unit == ''
    assert cfg.tolerance == {}
    assert cfg.attr == {}
    assert cfg.infoonly is False
    assert cfg.skip is False
    assert cfg.abortonfailure is False


def test_name_field():
    assert TestConfig.from_dict({'name': 'MyTest'}).name == 'MyTest'


def test_unit_and_x_unit():
    cfg = TestConfig.from_dict({'unit': 'V', 'x_unit': 's'})
    assert cfg.unit == 'V'
    assert cfg.x_unit == 's'


def test_tolerance_preserved():
    tol = {'min': 1.0, 'max': 2.0, 'expected': 'hello'}
    assert TestConfig.from_dict({'tolerance': tol}).tolerance == tol


def test_attr_preserved():
    attr = {'key': 'val', 'num': 42}
    assert TestConfig.from_dict({'attr': attr}).attr == attr


def test_infoonly_true():
    assert TestConfig.from_dict({'infoonly': True}).infoonly is True


def test_skip_true():
    assert TestConfig.from_dict({'skip': True}).skip is True


def test_abortonfailure_true():
    assert TestConfig.from_dict({'abortonfailure': True}).abortonfailure is True


def test_all_fields_together():
    d = {
        'name': 'Full',
        'unit': 'A',
        'x_unit': 'Hz',
        'tolerance': {'min': 0, 'max': 5},
        'attr': {'k': 'v'},
        'infoonly': True,
        'skip': True,
        'abortonfailure': True,
    }
    cfg = TestConfig.from_dict(d)
    assert cfg.name == 'Full'
    assert cfg.unit == 'A'
    assert cfg.x_unit == 'Hz'
    assert cfg.tolerance == {'min': 0, 'max': 5}
    assert cfg.attr == {'k': 'v'}
    assert cfg.infoonly is True
    assert cfg.skip is True
    assert cfg.abortonfailure is True


def test_unknown_keys_are_ignored():
    # Should not raise even with unrecognised keys
    cfg = TestConfig.from_dict({'name': 'X', 'unknown_key': 'should_be_ignored'})
    assert cfg.name == 'X'
    assert not hasattr(cfg, 'unknown_key')

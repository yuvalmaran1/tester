"""Integration tests for SQLiteDatabase: CRUD, role filter, query, migration."""
import sqlite3
import pytest
import pyjson5 as json

from tester.database.sqlite_db import SQLiteDatabase
from tester.TestRun import TestRun
from tester.TestResult import TestResult
from tester.TestConfig import TestConfig
from tester.TestResults.NumericTestResult import NumericTestResult
from tester.TestResults.PassFailTestResult import PassFailTestResult

E = TestResult.TestEval


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def db(tmp_path):
    return SQLiteDatabase(str(tmp_path / "test.db"))


def _run(dut='DUT', program='Prog'):
    run = TestRun(
        tester={'name': 'T', 'version': '1.0'},
        dut={'name': dut, 'description': 'desc', 'product_id': 'p1', 'image': ''},
        program={'name': program, 'description': 'pdesc', 'attr': {}},
    )
    run.start()
    run.end()
    return run


def _result(name='Test', *, eval_val=E.PASS, role='testcase'):
    cfg = TestConfig(attr={}, tolerance={'min': 0, 'max': 1}, unit='', name=name)
    r = NumericTestResult(cfg, 0.5, suite='Suite')
    r.role = role
    r.result = eval_val
    return r


# ── Basic CRUD ────────────────────────────────────────────────────────────────

def test_create_run_returns_id(db):
    run_id = db.create_run(_run())
    assert isinstance(run_id, int)
    assert run_id > 0


def test_get_run_fields(db):
    run_id = db.create_run(_run('MyDUT', 'MyProg'))
    retrieved = db.get_run(run_id)
    assert retrieved.dut == 'MyDUT'
    assert retrieved.program == 'MyProg'


def test_get_run_not_found_raises(db):
    with pytest.raises(ValueError):
        db.get_run(9999)


def test_append_result_stored(db):
    run_id = db.create_run(_run())
    db.append_result(_result('TC1'), run_id)
    retrieved = db.get_run(run_id)
    assert len(retrieved.test_results) == 1
    assert retrieved.test_results[0].name == 'TC1'


def test_append_multiple_results(db):
    run_id = db.create_run(_run())
    db.append_result(_result('A'), run_id)
    db.append_result(_result('B'), run_id)
    retrieved = db.get_run(run_id)
    names = [r.name for r in retrieved.test_results]
    assert 'A' in names and 'B' in names


def test_update_run_end_stores_program_modified(db):
    run = _run()
    run_id = db.create_run(run)
    run.run_id = run_id
    run.program_modified = True
    db.update_run_end(run)
    assert db.get_run(run_id).program_modified is True


def test_update_run_end_false_stays_false(db):
    run = _run()
    run_id = db.create_run(run)
    run.run_id = run_id
    run.program_modified = False
    db.update_run_end(run)
    assert db.get_run(run_id).program_modified is False


# ── get_runs ──────────────────────────────────────────────────────────────────

def test_get_runs_returns_json_string(db):
    db.create_run(_run('D1', 'P1'))
    runs = json.loads(db.get_runs())
    assert isinstance(runs, list)
    assert len(runs) == 1
    assert runs[0]['dut'] == 'D1'


def test_get_runs_multiple(db):
    db.create_run(_run('D1', 'P1'))
    db.create_run(_run('D2', 'P2'))
    runs = json.loads(db.get_runs())
    assert len(runs) == 2


# ── Role-based filtering: get_available_tests ─────────────────────────────────

def test_available_tests_excludes_setup_role(db):
    run_id = db.create_run(_run())
    db.append_result(_result('Setup TC', role='setup'), run_id)
    db.append_result(_result('Real TC', role='testcase'), run_id)
    tests = db.get_available_tests()
    assert 'Real TC' in tests
    assert 'Setup TC' not in tests


def test_available_tests_excludes_cleanup_role(db):
    run_id = db.create_run(_run())
    db.append_result(_result('Cleanup TC', role='cleanup'), run_id)
    db.append_result(_result('Real TC', role='testcase'), run_id)
    tests = db.get_available_tests()
    assert 'Real TC' in tests
    assert 'Cleanup TC' not in tests


def test_available_tests_deduplication(db):
    run_id1 = db.create_run(_run())
    run_id2 = db.create_run(_run())
    db.append_result(_result('TC1'), run_id1)
    db.append_result(_result('TC1'), run_id2)
    tests = db.get_available_tests()
    assert tests.count('TC1') == 1


def test_available_tests_empty_db(db):
    assert db.get_available_tests() == []


# ── get_available_programs / duts ─────────────────────────────────────────────

def test_available_programs_deduplication(db):
    db.create_run(_run('D', 'ProgA'))
    db.create_run(_run('D', 'ProgA'))   # duplicate
    db.create_run(_run('D', 'ProgB'))
    progs = db.get_available_programs()
    assert progs.count('ProgA') == 1
    assert 'ProgB' in progs


def test_available_duts_deduplication(db):
    db.create_run(_run('DUT_A', 'P'))
    db.create_run(_run('DUT_A', 'P'))   # duplicate
    db.create_run(_run('DUT_B', 'P'))
    duts = db.get_available_duts()
    assert duts.count('DUT_A') == 1
    assert 'DUT_B' in duts


# ── query_test_results ────────────────────────────────────────────────────────

def test_query_by_dut(db):
    run_a = db.create_run(_run('DUT_A', 'P'))
    run_b = db.create_run(_run('DUT_B', 'P'))
    db.append_result(_result('TC_A'), run_a)
    db.append_result(_result('TC_B'), run_b)
    results = db.query_test_results({'dut': 'DUT_A'})
    assert len(results) == 1
    assert results[0]['Name'] == 'TC_A'


def test_query_by_program(db):
    run1 = db.create_run(_run('D', 'Prog1'))
    run2 = db.create_run(_run('D', 'Prog2'))
    db.append_result(_result('TC1'), run1)
    db.append_result(_result('TC2'), run2)
    results = db.query_test_results({'program': 'Prog1'})
    assert len(results) == 1
    assert results[0]['Name'] == 'TC1'


def test_query_by_test_name(db):
    run_id = db.create_run(_run())
    db.append_result(_result('TC_Alpha'), run_id)
    db.append_result(_result('TC_Beta'), run_id)
    results = db.query_test_results({'test_name': 'TC_Alpha'})
    assert len(results) == 1
    assert results[0]['Name'] == 'TC_Alpha'


def test_query_excludes_setup_and_cleanup_roles(db):
    run_id = db.create_run(_run())
    db.append_result(_result('Setup', role='setup'), run_id)
    db.append_result(_result('TC', role='testcase'), run_id)
    db.append_result(_result('Cleanup', role='cleanup'), run_id)
    results = db.query_test_results({})
    names = [r['Name'] for r in results]
    assert 'TC' in names
    assert 'Setup' not in names
    assert 'Cleanup' not in names


def test_query_result_includes_dut_and_program(db):
    run_id = db.create_run(_run('My DUT', 'My Prog'))
    db.append_result(_result('TC'), run_id)
    results = db.query_test_results({})
    assert results[0]['DUT'] == 'My DUT'
    assert results[0]['Program'] == 'My Prog'


def test_query_multiple_test_names(db):
    run_id = db.create_run(_run())
    db.append_result(_result('A'), run_id)
    db.append_result(_result('B'), run_id)
    db.append_result(_result('C'), run_id)
    results = db.query_test_results({'test_names': 'A,B'})
    names = {r['Name'] for r in results}
    assert names == {'A', 'B'}


# ── Migration: role column added to existing DB ───────────────────────────────

def test_migration_adds_role_column(tmp_path):
    """A pre-existing DB without a role column is migrated transparently."""
    db_path = str(tmp_path / "legacy.db")

    # Create a DB whose results table lacks the role column
    with sqlite3.connect(db_path) as con:
        con.execute(
            "CREATE TABLE results("
            "result_id integer primary key autoincrement, run_id integer, "
            "date text, suite text, name text, tolerance text, value text, "
            "unit text, result text, comment text, infoonly integer, skip integer, "
            "attr text, result_type text)"
        )
        con.execute(
            "CREATE TABLE runs("
            "run_id integer primary key autoincrement, tester text, tester_ver text, "
            "dut text, dut_desc text, dut_product_id text, dut_image text, "
            "program text, program_desc text, start_date text, end_date text, "
            "result text, log text, attachment blob)"
        )
        con.commit()

    # Opening via SQLiteDatabase must migrate without raising
    SQLiteDatabase(db_path)

    with sqlite3.connect(db_path) as con:
        cols = [row[1] for row in con.execute("PRAGMA table_info(results)").fetchall()]
    assert 'role' in cols


def test_migration_program_modified_column(tmp_path):
    """A pre-existing runs table without program_modified is migrated."""
    db_path = str(tmp_path / "legacy2.db")
    with sqlite3.connect(db_path) as con:
        con.execute(
            "CREATE TABLE runs("
            "run_id integer primary key autoincrement, tester text, tester_ver text, "
            "dut text, dut_desc text, dut_product_id text, dut_image text, "
            "program text, program_desc text, start_date text, end_date text, "
            "result text, log text, attachment blob)"
        )
        con.execute(
            "CREATE TABLE results("
            "result_id integer primary key autoincrement, run_id integer, "
            "date text, suite text, name text, tolerance text, value text, "
            "unit text, result text, comment text, infoonly integer, skip integer, "
            "attr text, result_type text, role text)"
        )
        con.commit()

    SQLiteDatabase(db_path)

    with sqlite3.connect(db_path) as con:
        cols = [row[1] for row in con.execute("PRAGMA table_info(runs)").fetchall()]
    assert 'program_modified' in cols

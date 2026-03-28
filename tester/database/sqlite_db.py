import sqlite3
import pyjson5 as json
from contextlib import contextmanager
from typing import List, Dict, Any
from .base import DatabaseInterface
from ..TestResult import TestResult
from ..TestRun import TestRun
from ..TestResultFactory import TestResultFactory


class SQLiteDatabase(DatabaseInterface):
    """SQLite database implementation."""

    RUNS_TABLE = "runs"
    RUNS_COLS_DEF = "run_id integer primary key autoincrement, tester text, tester_ver text, dut text, dut_desc text, dut_product_id text, dut_image text, program text, program_desc text, start_date text, end_date text, result text, log text, attachment blob, program_modified integer, program_attr text, operator text"
    RUNS_COLS = "tester, tester_ver, dut, dut_desc, dut_product_id, dut_image, program, program_desc, start_date, end_date, result, log, attachment, program_modified, program_attr, operator"
    RUNS_REPORT_COLS = "run_id, dut, program, start_date, end_date, result, operator"
    RESULT_TABLE = "results"
    RESULT_COLS_DEF = "result_id integer primary key autoincrement, run_id integer, date text, suite text, name text, tolerance text, value text, unit text, result text, comment text, infoonly integer, skip integer, attr text, result_type text, role text"
    RESULT_COLS = "run_id, date, suite, name, tolerance, value, unit, result, comment, infoonly, skip, attr, result_type, role"
    OPERATORS_TABLE = "operators"
    OPERATORS_COLS_DEF = "operator_id integer primary key autoincrement, username text unique not null, display_name text, password_hash text, role text default 'operator', active integer default 1"
    OPERATORS_COLS = "username, display_name, password_hash, role, active"

    def __init__(self, config_string: str):
        """Initialize SQLite database connection.

        Args:
            config_string: SQLite database file path (e.g., "./test.db")
        """
        self.db_file = config_string
        self._init_tables()

    @contextmanager
    def _connect(self):
        con = sqlite3.connect(self.db_file)
        try:
            yield con
        finally:
            con.close()

    def _init_tables(self):
        """Initialize database tables."""
        with self._connect() as con:
            cursor = con.cursor()

            # Create runs table
            cursor.execute(f'CREATE TABLE IF NOT EXISTS {self.RUNS_TABLE}({self.RUNS_COLS_DEF})')

            # Create results table
            cursor.execute(f'CREATE TABLE IF NOT EXISTS {self.RESULT_TABLE}({self.RESULT_COLS_DEF})')

            # Create operators table
            cursor.execute(f'CREATE TABLE IF NOT EXISTS {self.OPERATORS_TABLE}({self.OPERATORS_COLS_DEF})')

            # Check if program_modified column exists, add it if not (migration)
            cursor.execute(f"PRAGMA table_info({self.RUNS_TABLE})")
            columns = [column[1] for column in cursor.fetchall()]
            if 'program_modified' not in columns:
                cursor.execute(f'ALTER TABLE {self.RUNS_TABLE} ADD COLUMN program_modified integer')
                print("Added program_modified column to existing database")

            # Check if program_attr column exists, add it if not (migration)
            if 'program_attr' not in columns:
                cursor.execute(f'ALTER TABLE {self.RUNS_TABLE} ADD COLUMN program_attr text')
                print("Added program_attr column to existing database")

            # Check if operator column exists, add it if not (migration)
            if 'operator' not in columns:
                cursor.execute(f'ALTER TABLE {self.RUNS_TABLE} ADD COLUMN operator text')
                print("Added operator column to existing database")

            # Check if role column exists in results table, add it if not (migration)
            cursor.execute(f"PRAGMA table_info({self.RESULT_TABLE})")
            result_columns = [column[1] for column in cursor.fetchall()]
            if 'role' not in result_columns:
                cursor.execute(f"ALTER TABLE {self.RESULT_TABLE} ADD COLUMN role text DEFAULT 'testcase'")
                print("Added role column to existing database")

            con.commit()

    def create_run(self, run: TestRun) -> int:
        """Create a new test run and return the run ID."""
        with self._connect() as con:
            cursor = con.cursor()
            entities = (run.tester, run.tester_ver, run.dut, run.dut_desc, run.dut_product_id,
                       run.dut_image, run.program, run.program_desc, str(run.start_date),
                       str(run.end_date), str(run.result), json.dumps(run.log), run.attachment.getvalue(),
                       int(getattr(run, 'program_modified', False)), json.dumps(getattr(run, 'program_attr', {})),
                       getattr(run, 'operator', ''))
            cursor.execute(f'INSERT INTO {self.RUNS_TABLE}({self.RUNS_COLS}) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', entities)
            run_id = cursor.lastrowid
            con.commit()
            return run_id

    def update_run_end(self, run: TestRun) -> None:
        """Update the end time and result of a test run."""
        with self._connect() as con:
            cursor = con.cursor()
            cursor.execute(f'UPDATE {self.RUNS_TABLE} SET end_date = ?, result = ?, log = ?, attachment = ?, program_modified = ? WHERE run_id = ?',
                          (str(run.end_date), str(run.result), json.dumps(run.log), run.attachment.getvalue(),
                           int(getattr(run, 'program_modified', False)), run.run_id))
            con.commit()

    def append_result(self, result: TestResult, run_id: int) -> None:
        """Append a test result to a specific run."""
        with self._connect() as con:
            cursor = con.cursor()
            entities = (run_id, str(result.date), result.suite, result.name, json.dumps(result.tolerance),
                       str(result.value), result.unit, str(result.result), result.comment,
                       result.infoonly, result.skip, str(result.attr), result.result_type,
                       getattr(result, 'role', 'testcase'))
            cursor.execute(f'INSERT INTO {self.RESULT_TABLE}({self.RESULT_COLS}) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)', entities)
            con.commit()

    def get_run(self, run_id: int) -> TestRun:
        """Get a complete test run with all its results."""
        with self._connect() as con:
            cursor = con.cursor()
            cursor.execute(f'SELECT {self.RUNS_COLS} FROM {self.RUNS_TABLE} WHERE run_id = {run_id}')
            run = cursor.fetchone()
            cursor.execute(f'SELECT {self.RESULT_COLS} FROM {self.RESULT_TABLE} WHERE run_id = {run_id}')
            results = cursor.fetchall()

            if not run:
                raise ValueError(f"Run with ID {run_id} not found")

            run_keys = self.RUNS_COLS.replace(' ', '').split(',')
            run_dict = {run_keys[i]: run[i] for i in range(len(run_keys))}
            try:
                run_dict['log'] = json.loads(run_dict['log']) if run_dict['log'] else []
            except (json.Json5DecoderException, json.Json5Exception, TypeError, ValueError):
                run_dict['log'] = []

            run_dict['program_modified'] = bool(run_dict.get('program_modified', 0))

            try:
                run_dict['program_attr'] = json.loads(run_dict.get('program_attr', '{}'))
            except (json.Json5DecoderException, json.Json5Exception, TypeError, ValueError):
                run_dict['program_attr'] = {}

            result_keys = self.RESULT_COLS.replace(' ', '').split(',')
            result_dicts = []
            for r in results:
                result_dicts.append({result_keys[i]: r[i] for i in range(len(result_keys))})

            return TestRun.from_dict(run_dict, result_dicts)

    def get_runs(self) -> str:
        """Get all test runs as JSON string."""
        with self._connect() as con:
            cursor = con.cursor()
            cursor.execute(f'SELECT {self.RUNS_REPORT_COLS} FROM {self.RUNS_TABLE}')
            runs = cursor.fetchall()

            run_keys = self.RUNS_REPORT_COLS.replace(' ', '').split(',')
            runs_dict = []
            for r in runs:
                runs_dict.append({run_keys[i]: r[i] for i in range(len(run_keys))})

            return json.dumps(runs_dict)

    def get_available_tests(self) -> list:
        """Get list of all unique test names, excluding setup and cleanup tests."""
        with self._connect() as con:
            cursor = con.cursor()
            cursor.execute(f'''
                SELECT DISTINCT name FROM {self.RESULT_TABLE}
                WHERE role = 'testcase'
                ORDER BY name
            ''')
            tests = cursor.fetchall()
            return [test[0] for test in tests]

    def get_available_programs(self) -> list:
        """Get list of all unique program names."""
        with self._connect() as con:
            cursor = con.cursor()
            cursor.execute(f'SELECT DISTINCT program FROM {self.RUNS_TABLE} ORDER BY program')
            programs = cursor.fetchall()
            return [program[0] for program in programs]

    def get_available_duts(self) -> list:
        """Get list of all unique DUT names."""
        with self._connect() as con:
            cursor = con.cursor()
            cursor.execute(f'SELECT DISTINCT dut FROM {self.RUNS_TABLE} ORDER BY dut')
            duts = cursor.fetchall()
            return [dut[0] for dut in duts]

    def query_test_results(self, query_params: dict) -> list:
        """Query test results with filters."""
        with self._connect() as con:
            cursor = con.cursor()

            # Build the query - join results with runs to get DUT and program info
            query = f'''
                SELECT res.run_id, res.date, res.suite, res.name, res.tolerance, res.value, res.unit, res.result, res.comment, res.infoonly, res.skip, res.attr, res.result_type, res.role, r.dut, r.program
                FROM {self.RESULT_TABLE} res
                JOIN {self.RUNS_TABLE} r ON res.run_id = r.run_id
                WHERE 1=1
            '''

            # Build filters using common method
            filters, params = self._build_query_filters(query_params, '?')

            # Add filters to query
            for filter_clause in filters:
                query += ' AND ' + filter_clause

            query += ' ORDER BY res.date DESC'

            cursor.execute(query, params)
            results = cursor.fetchall()

            # Convert to TestResult objects using TestResultFactory
            results_list = []
            result_keys = self.RESULT_COLS.replace(' ', '').split(',')

            for r in results:
                # Map result columns (first N columns are from results table)
                result_dict = {result_keys[i]: r[i] for i in range(len(result_keys))}

                # Extract DUT and program from the additional columns
                dut = r[len(result_keys)]      # DUT is the next column after result columns
                program = r[len(result_keys) + 1]  # Program is the column after DUT

                # Reconstruct TestResult object
                try:
                    test_result_dict = TestResultFactory().from_dict(result_dict).to_dict()
                    # Add DUT, program, and run_id info to the result
                    test_result_dict['DUT'] = dut
                    test_result_dict['Program'] = program
                    test_result_dict['run_id'] = result_dict['run_id']
                    results_list.append(test_result_dict)
                except Exception as e:
                    print(f"Warning: Failed to reconstruct TestResult for {result_dict.get('name', 'unknown')}: {e}")
                    # Skip this result if reconstruction fails
                    continue

            return results_list

    # ── Operator management ───────────────────────────────────────────────────

    def list_operators(self) -> list:
        with self._connect() as con:
            cursor = con.cursor()
            cursor.execute(f'SELECT operator_id, username, display_name, role, active FROM {self.OPERATORS_TABLE} ORDER BY username')
            rows = cursor.fetchall()
            return [{'id': r[0], 'username': r[1], 'display_name': r[2], 'role': r[3], 'active': bool(r[4])} for r in rows]

    def get_operator_by_username(self, username: str) -> dict | None:
        with self._connect() as con:
            cursor = con.cursor()
            cursor.execute(f'SELECT operator_id, username, display_name, password_hash, role, active FROM {self.OPERATORS_TABLE} WHERE username = ?', (username,))
            row = cursor.fetchone()
            if not row:
                return None
            return {'id': row[0], 'username': row[1], 'display_name': row[2], 'password_hash': row[3], 'role': row[4], 'active': bool(row[5])}

    def add_operator(self, username: str, display_name: str, password_hash: str, role: str = 'operator') -> dict:
        with self._connect() as con:
            cursor = con.cursor()
            cursor.execute(f'INSERT INTO {self.OPERATORS_TABLE}({self.OPERATORS_COLS}) VALUES(?,?,?,?,?)',
                           (username, display_name, password_hash, role, 1))
            op_id = cursor.lastrowid
            con.commit()
            return {'id': op_id, 'username': username, 'display_name': display_name, 'role': role, 'active': True}

    def update_operator(self, operator_id: int, display_name: str, role: str, active: bool) -> dict:
        with self._connect() as con:
            cursor = con.cursor()
            cursor.execute(f'UPDATE {self.OPERATORS_TABLE} SET display_name=?, role=?, active=? WHERE operator_id=?',
                           (display_name, role, int(active), operator_id))
            con.commit()
            cursor.execute(f'SELECT operator_id, username, display_name, role, active FROM {self.OPERATORS_TABLE} WHERE operator_id=?', (operator_id,))
            row = cursor.fetchone()
            return {'id': row[0], 'username': row[1], 'display_name': row[2], 'role': row[3], 'active': bool(row[4])}

    def update_operator_password(self, operator_id: int, password_hash: str) -> None:
        with self._connect() as con:
            cursor = con.cursor()
            cursor.execute(f'UPDATE {self.OPERATORS_TABLE} SET password_hash=? WHERE operator_id=?', (password_hash, operator_id))
            con.commit()

    def delete_operator(self, operator_id: int) -> None:
        with self._connect() as con:
            cursor = con.cursor()
            cursor.execute(f'DELETE FROM {self.OPERATORS_TABLE} WHERE operator_id=?', (operator_id,))
            con.commit()

    def close(self) -> None:
        """Close database connection (no-op for SQLite as we use context managers)."""
        pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

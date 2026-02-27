import psycopg2
import psycopg2.pool
import pyjson5 as json
from urllib.parse import urlparse, parse_qs
from typing import List, Dict, Any, Optional
from .base import DatabaseInterface
from ..TestResult import TestResult
from ..TestRun import TestRun


class PostgreSQLDatabase(DatabaseInterface):
    """PostgreSQL database implementation with connection pooling."""

    RUNS_TABLE = "runs"
    RUNS_COLS_DEF = "run_id SERIAL PRIMARY KEY, tester TEXT, tester_ver TEXT, dut TEXT, dut_desc TEXT, dut_product_id TEXT, dut_image TEXT, program TEXT, program_desc TEXT, start_date TEXT, end_date TEXT, result TEXT, log TEXT, attachment BYTEA, program_modified BOOLEAN, program_attr TEXT"
    RUNS_COLS = "tester, tester_ver, dut, dut_desc, dut_product_id, dut_image, program, program_desc, start_date, end_date, result, log, attachment, program_modified, program_attr"
    RUNS_REPORT_COLS = "run_id, dut, program, start_date, end_date, result"
    RESULT_TABLE = "results"
    RESULT_COLS_DEF = "result_id SERIAL PRIMARY KEY, run_id INTEGER, date TEXT, suite TEXT, name TEXT, tolerance TEXT, value TEXT, unit TEXT, result TEXT, comment TEXT, infoonly INTEGER, skip INTEGER, attr TEXT, result_type TEXT"
    RESULT_COLS = "run_id, date, suite, name, tolerance, value, unit, result, comment, infoonly, skip, attr, result_type"

    def __init__(self, config_string: str):
        """Initialize PostgreSQL database connection.

        Args:
            config_string: PostgreSQL connection string (e.g., "postgresql://user:pass@host:port/db")
        """
        self.config = self._parse_connection_string(config_string)
        self.pool = None
        self._init_connection_pool()
        self._init_tables()

    def _parse_connection_string(self, config_string: str) -> Dict[str, Any]:
        """Parse PostgreSQL connection string."""
        parsed = urlparse(config_string)
        query_params = parse_qs(parsed.query)

        config = {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path[1:],  # Remove leading slash
            'user': parsed.username,
            'password': parsed.password,
        }

        # Add query parameters
        for key, value in query_params.items():
            if len(value) == 1:
                config[key] = value[0]
            else:
                config[key] = value

        return config

    def _init_connection_pool(self):
        """Initialize connection pool."""
        try:
            self.pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=5,  # Adjust based on your needs
                **self.config
            )
        except psycopg2.Error as e:
            raise ConnectionError(f"Failed to connect to PostgreSQL database: {e}")

    def _get_connection(self):
        """Get a connection from the pool."""
        if not self.pool:
            raise ConnectionError("Database connection pool not initialized")
        return self.pool.getconn()

    def _return_connection(self, conn):
        """Return a connection to the pool."""
        if self.pool:
            self.pool.putconn(conn)

    def _init_tables(self):
        """Initialize database tables."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                # Create runs table
                cursor.execute(f'CREATE TABLE IF NOT EXISTS {self.RUNS_TABLE}({self.RUNS_COLS_DEF})')

                # Create results table
                cursor.execute(f'CREATE TABLE IF NOT EXISTS {self.RESULT_TABLE}({self.RESULT_COLS_DEF})')

                # Check if program_modified column exists, add it if not (migration)
                cursor.execute(f"""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = '{self.RUNS_TABLE}' AND column_name = 'program_modified'
                """)
                if not cursor.fetchone():
                    cursor.execute(f'ALTER TABLE {self.RUNS_TABLE} ADD COLUMN program_modified BOOLEAN')
                    print("Added program_modified column to existing PostgreSQL database")

                # Check if program_attr column exists, add it if not (migration)
                cursor.execute(f"""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = '{self.RUNS_TABLE}' AND column_name = 'program_attr'
                """)
                if not cursor.fetchone():
                    cursor.execute(f'ALTER TABLE {self.RUNS_TABLE} ADD COLUMN program_attr TEXT')
                    print("Added program_attr column to existing PostgreSQL database")

                conn.commit()
        finally:
            self._return_connection(conn)

    def create_run(self, run: TestRun) -> int:
        """Create a new test run and return the run ID."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                entities = (run.tester, run.tester_ver, run.dut, run.dut_desc, run.dut_product_id,
                           run.dut_image, run.program, run.program_desc, run.start_date,
                           run.end_date, str(run.result), json.dumps(run.log), run.attachment.getvalue(),
                           getattr(run, 'program_modified', False), json.dumps(getattr(run, 'program_attr', {})))
                cursor.execute(f'INSERT INTO {self.RUNS_TABLE}({self.RUNS_COLS}) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING run_id', entities)
                run_id = cursor.fetchone()[0]
                conn.commit()
                return run_id
        finally:
            self._return_connection(conn)

    def update_run_end(self, run: TestRun) -> None:
        """Update the end time and result of a test run."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(f'UPDATE {self.RUNS_TABLE} SET end_date = %s, result = %s, log = %s, attachment = %s, program_modified = %s WHERE run_id = %s',
                              (run.end_date, str(run.result), json.dumps(run.log), run.attachment.getvalue(),
                               getattr(run, 'program_modified', False), run.run_id))
                conn.commit()
        finally:
            self._return_connection(conn)

    def append_result(self, result: TestResult, run_id: int) -> None:
        """Append a test result to a specific run."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                entities = (run_id, result.date, result.suite, result.name, json.dumps(result.tolerance),
                           str(result.value), result.unit, str(result.result), result.comment,
                           result.infoonly, result.skip, str(result.attr), result.result_type)
                cursor.execute(f'INSERT INTO {self.RESULT_TABLE}({self.RESULT_COLS}) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', entities)
                conn.commit()
        finally:
            self._return_connection(conn)

    def get_run(self, run_id: int) -> TestRun:
        """Get a complete test run with all its results."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(f'SELECT {self.RUNS_COLS} FROM {self.RUNS_TABLE} WHERE run_id = %s', (run_id,))
                run = cursor.fetchone()
                cursor.execute(f'SELECT {self.RESULT_COLS} FROM {self.RESULT_TABLE} WHERE run_id = %s', (run_id,))
                results = cursor.fetchall()

                if not run:
                    raise ValueError(f"Run with ID {run_id} not found")

                run_keys = self.RUNS_COLS.replace(' ', '').split(',')
                run_dict = {run_keys[i]: run[i] for i in range(len(run_keys))}
                try:
                    run_dict['log'] = json.loads(run_dict['log']) if run_dict['log'] else []
                except (json.Json5DecoderException, json.Json5Exception, TypeError, ValueError):
                    run_dict['log'] = []

                run_dict['program_modified'] = bool(run_dict.get('program_modified', False))

                try:
                    run_dict['program_attr'] = json.loads(run_dict.get('program_attr', '{}'))
                except (json.Json5DecoderException, json.Json5Exception, TypeError, ValueError):
                    run_dict['program_attr'] = {}

                result_keys = self.RESULT_COLS.replace(' ', '').split(',')
                result_dicts = []
                for r in results:
                    result_dicts.append({result_keys[i]: r[i] for i in range(len(result_keys))})

                return TestRun.from_dict(run_dict, result_dicts)
        finally:
            self._return_connection(conn)

    def get_runs(self) -> str:
        """Get all test runs as JSON string."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(f'SELECT {self.RUNS_REPORT_COLS} FROM {self.RUNS_TABLE}')
                runs = cursor.fetchall()

                run_keys = self.RUNS_REPORT_COLS.replace(' ', '').split(',')
                runs_dict = []
                for r in runs:
                    runs_dict.append({run_keys[i]: r[i] for i in range(len(run_keys))})

                return json.dumps(runs_dict)
        finally:
            self._return_connection(conn)

    def get_available_tests(self) -> list:
        """Get list of all unique test names, excluding setup and cleanup tests."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(f'''
                    SELECT DISTINCT name FROM {self.RESULT_TABLE}
                    WHERE name NOT ILIKE '%setup%' AND name NOT ILIKE '%cleanup%'
                    ORDER BY name
                ''')
                tests = cursor.fetchall()
                return [test[0] for test in tests]
        finally:
            self._return_connection(conn)

    def get_available_programs(self) -> list:
        """Get list of all unique program names."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(f'SELECT DISTINCT program FROM {self.RUNS_TABLE} ORDER BY program')
                programs = cursor.fetchall()
                return [program[0] for program in programs]
        finally:
            self._return_connection(conn)

    def get_available_duts(self) -> list:
        """Get list of all unique DUT names."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(f'SELECT DISTINCT dut FROM {self.RUNS_TABLE} ORDER BY dut')
                duts = cursor.fetchall()
                return [dut[0] for dut in duts]
        finally:
            self._return_connection(conn)

    def query_test_results(self, query_params: dict) -> list:
        """Query test results with filters."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                # Build the query - join results with runs to get DUT and program info
                query = f'''
                    SELECT res.run_id, res.date, res.suite, res.name, res.tolerance, res.value, res.unit, res.result, res.comment, res.infoonly, res.skip, res.attr, res.result_type, r.dut, r.program
                    FROM {self.RESULT_TABLE} res
                    JOIN {self.RUNS_TABLE} r ON res.run_id = r.run_id
                    WHERE 1=1
                '''

                # Build filters using common method
                filters, params = self._build_query_filters(query_params, '%s')

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
                        from ..TestResultFactory import TestResultFactory
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
        finally:
            self._return_connection(conn)

    def close(self) -> None:
        """Close database connection pool."""
        if self.pool:
            self.pool.closeall()
            self.pool = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

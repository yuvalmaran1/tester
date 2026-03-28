import re
import pyjson5 as json
from .TestResult import TestResult
from .TestRun import TestRun
from .database import DatabaseFactory


class TestDB:
    """Database wrapper that uses the appropriate database implementation based on configuration."""

    def __init__(self, config_string='test_results.db'):
        """Initialize database with configuration string.

        Args:
            config_string: Database configuration string
                - For SQLite: file path (e.g., "./test.db")
                - For PostgreSQL: connection string (e.g., "postgresql://user:pass@host:port/db")
        """
        self.db = DatabaseFactory.create_database(config_string)
        self.config_string = config_string

    def create_run(self, run: TestRun) -> int:
        """Create a new test run and return the run ID."""
        return self.db.create_run(run)

    def update_run_end(self, run: TestRun) -> None:
        """Update the end time and result of a test run."""
        self.db.update_run_end(run)

    def append_result(self, result: TestResult, run_id: int) -> None:
        """Append a test result to a specific run."""
        self.db.append_result(result, run_id)

    def get_run(self, run_id: int) -> TestRun:
        """Get a complete test run with all its results."""
        return self.db.get_run(run_id)

    def get_runs(self) -> str:
        """Get all test runs as JSON string."""
        return self.db.get_runs()

    def get_available_tests(self) -> list:
        """Get list of all unique test names."""
        return self.db.get_available_tests()

    def get_available_programs(self) -> list:
        """Get list of all unique program names."""
        return self.db.get_available_programs()

    def get_available_duts(self) -> list:
        """Get list of all unique DUT names."""
        return self.db.get_available_duts()

    def query_test_results(self, query_params: dict) -> list:
        """Query test results with filters."""
        return self.db.query_test_results(query_params)

    # ── Operator management ───────────────────────────────────────────────────

    def list_operators(self) -> list:
        return self.db.list_operators()

    def get_operator_by_username(self, username: str) -> dict | None:
        return self.db.get_operator_by_username(username)

    def add_operator(self, username: str, display_name: str, password_hash: str, role: str = 'operator') -> dict:
        return self.db.add_operator(username, display_name, password_hash, role)

    def update_operator(self, operator_id: int, display_name: str, role: str, active: bool) -> dict:
        return self.db.update_operator(operator_id, display_name, role, active)

    def update_operator_password(self, operator_id: int, password_hash: str) -> None:
        self.db.update_operator_password(operator_id, password_hash)

    def delete_operator(self, operator_id: int) -> None:
        self.db.delete_operator(operator_id)

    def close(self) -> None:
        """Close database connection."""
        self.db.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    # Backward compatibility methods
    def append_run(self, run: TestRun) -> int:
        """Backward compatibility method for append_run."""
        return self.create_run(run)

    def get_latest_run_id(self) -> int:
        """Get the latest run ID from the database."""
        runs_json = self.get_runs()
        try:
            runs = json.loads(runs_json)
        except (json.Json5DecoderException, json.Json5Exception, TypeError, ValueError):
            return 0
        if not runs:
            return 0
        return max(run['run_id'] for run in runs)

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ..TestResult import TestResult
from ..TestRun import TestRun


class DatabaseInterface(ABC):
    """Abstract base class for database implementations."""

    @abstractmethod
    def create_run(self, run: TestRun) -> int:
        """Create a new test run and return the run ID."""
        pass

    @abstractmethod
    def update_run_end(self, run: TestRun) -> None:
        """Update the end time and result of a test run."""
        pass

    @abstractmethod
    def append_result(self, result: TestResult, run_id: int) -> None:
        """Append a test result to a specific run."""
        pass

    @abstractmethod
    def get_run(self, run_id: int) -> TestRun:
        """Get a complete test run with all its results."""
        pass

    @abstractmethod
    def get_runs(self) -> str:
        """Get all test runs as JSON string."""
        pass

    @abstractmethod
    def get_available_tests(self) -> list:
        """Get list of all unique test names."""
        pass

    @abstractmethod
    def get_available_programs(self) -> list:
        """Get list of all unique program names."""
        pass

    @abstractmethod
    def get_available_duts(self) -> list:
        """Get list of all unique DUT names."""
        pass

    @abstractmethod
    def query_test_results(self, query_params: dict) -> list:
        """Query test results with filters."""
        pass

    def _build_query_filters(self, query_params: dict, param_placeholder: str = '?') -> tuple:
        """Build query filters and parameters for test results query.

        Args:
            query_params: Dictionary containing filter parameters
            param_placeholder: Placeholder for parameters ('?' for SQLite, '%s' for PostgreSQL)

        Returns:
            Tuple of (filter_clauses, parameters)
        """
        filters = []
        params = []

        # Handle multiple selections for test names
        if query_params.get('test_names'):
            test_names = query_params['test_names'].split(',')
            placeholders = ', '.join([param_placeholder] * len(test_names))
            filters.append(f'res.name IN ({placeholders})')
            params.extend(test_names)
        elif query_params.get('test_name'):
            filters.append('res.name = ' + param_placeholder)
            params.append(query_params['test_name'])

        # Handle multiple selections for programs
        if query_params.get('programs'):
            programs = query_params['programs'].split(',')
            placeholders = ', '.join([param_placeholder] * len(programs))
            filters.append(f'r.program IN ({placeholders})')
            params.extend(programs)
        elif query_params.get('program'):
            filters.append('r.program = ' + param_placeholder)
            params.append(query_params['program'])

        # Handle multiple selections for DUTs
        if query_params.get('duts'):
            duts = query_params['duts'].split(',')
            placeholders = ', '.join([param_placeholder] * len(duts))
            filters.append(f'r.dut IN ({placeholders})')
            params.extend(duts)
        elif query_params.get('dut'):
            filters.append('r.dut = ' + param_placeholder)
            params.append(query_params['dut'])

        # Handle multiple selections for results
        if query_params.get('results'):
            results = query_params['results'].split(',')
            placeholders = ', '.join([param_placeholder] * len(results))
            filters.append(f'res.result IN ({placeholders})')
            params.extend(results)
        elif query_params.get('result'):
            filters.append('res.result = ' + param_placeholder)
            params.append(query_params['result'])

        if query_params.get('start_date'):
            filters.append('res.date >= ' + param_placeholder)
            params.append(query_params['start_date'] + ' 00:00:00')

        if query_params.get('end_date'):
            filters.append('res.date <= ' + param_placeholder)
            params.append(query_params['end_date'] + ' 23:59:59')

        # Always exclude setup and cleanup tests (identified by explicit role column)
        filters.append('res.role = ' + param_placeholder)
        params.append('testcase')

        return filters, params

    # ── Operator management ───────────────────────────────────────────────────

    @abstractmethod
    def list_operators(self) -> list:
        """Return all operators as a list of dicts."""
        pass

    @abstractmethod
    def get_operator_by_username(self, username: str) -> dict | None:
        """Return a single operator dict (including password_hash) or None."""
        pass

    @abstractmethod
    def add_operator(self, username: str, display_name: str, password_hash: str, role: str = 'operator') -> dict:
        """Insert a new operator and return it as a dict."""
        pass

    @abstractmethod
    def update_operator(self, operator_id: int, display_name: str, role: str, active: bool) -> dict:
        """Update display_name, role and active flag; return updated dict."""
        pass

    @abstractmethod
    def update_operator_password(self, operator_id: int, password_hash: str) -> None:
        """Replace the password hash for an operator."""
        pass

    @abstractmethod
    def delete_operator(self, operator_id: int) -> None:
        """Permanently delete an operator."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close database connection."""
        pass

    @abstractmethod
    def __enter__(self):
        """Context manager entry."""
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass

import os
from tester import Tester
from tester.TestLogger import TestLogger
from tester.TesterConfig import TesterConfig


class ExampleTesterPostgreSQL(Tester):
    """Example tester configured to use PostgreSQL/Supabase database."""

    def __init__(self, ui=True) -> None:
        # Get database configuration from environment variable
        # For Supabase: postgresql://postgres:password@db.project.supabase.co:5432/postgres
        # For local PostgreSQL: postgresql://user:password@localhost:5432/database_name
        db_config = os.getenv('DATABASE_URL', './TestDB.db')  # Fallback to SQLite

        cfg = TesterConfig(
            name="ExampleTesterPostgreSQL",
            description="Production Tester with PostgreSQL/Supabase",
            version="0.0.1",
            db_config=db_config,
            setup_file="./setup.json",
            duts_file="./duts.json",
            log_dir=None,
            ui=ui
        )

        super().__init__(cfg)

    def _init(self, setup: dict) -> dict:
        """Initialize tester assets."""
        return {}


if __name__ == '__main__':
    # Example usage:
    # Set environment variable: DATABASE_URL=postgresql://postgres:password@db.project.supabase.co:5432/postgres
    # Or for local PostgreSQL: DATABASE_URL=postgresql://user:password@localhost:5432/test_framework
    ExampleTesterPostgreSQL()

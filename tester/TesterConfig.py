from dataclasses import dataclass, field
import pathlib

@dataclass
class TesterConfig:
    db_config: str  # Database configuration string (file path for SQLite, connection string for PostgreSQL)
    setup_file: str
    duts_file: str
    log_dir: str = field(default='./logs')
    ui: bool = field(default=True)
    name: str = field(default='Tester')
    description: str = field(default='Tester description')
    version: str = field(default='0.0.0')

    # Backward compatibility property
    @property
    def db_file(self) -> str:
        """Backward compatibility property for db_file."""
        return self.db_config

from dataclasses import dataclass, field
from typing import Optional, Type
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
    # Per-station hardware configuration (replaces setup_file for typed configs)
    station_config_file: Optional[str] = field(default=None)
    station_config_class: Optional[Type] = field(default=None)
    debug_reload: bool = field(default=False)

    # Backward compatibility property
    @property
    def db_file(self) -> str:
        """Backward compatibility property for db_file."""
        return self.db_config

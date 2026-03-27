from dataclasses import dataclass

from tester import Tester
from tester.TesterConfig import TesterConfig
from tester.StationConfig import StationConfig


class ExampleStationConfig(StationConfig):
    """Per-station hardware configuration for the example tester.

    Each test station provides its own station.json with these values.
    Fields have defaults so the file can be empty ({}) for simple setups.
    """
    serial_port: str = "COM1"
    ip_address: str = "127.0.0.1"


@dataclass
class ExampleAssets:
    """Hardware handles opened once at startup and shared across all test cases.

    Add one field per instrument or connection. Type annotations enable
    IDE auto-complete inside every _execute() that receives these assets.
    """
    # instrument: MyInstrument   # example — uncomment and replace
    pass


class ExampleTester(Tester):
    def __init__(self, ui=True) -> None:
        cfg = TesterConfig(
            name="Example Tester",
            description="Production Tester",
            version="0.0.1",
            db_config="./TestDB.db",
            setup_file="./setup.json",
            duts_file="./duts.json",
            log_dir=None,
            ui=ui,
            station_config_file="./station.json",
            station_config_class=ExampleStationConfig,
        )
        super().__init__(cfg)

    def _init(self, station_config: ExampleStationConfig) -> ExampleAssets:
        # Open hardware connections here and store them as dataclass fields.
        # e.g. return ExampleAssets(instrument=MyInstrument(station_config.serial_port))
        return ExampleAssets()


if __name__ == '__main__':
    ExampleTester()

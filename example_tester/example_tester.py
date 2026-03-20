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

    def _init(self, station_config: ExampleStationConfig) -> dict:
        # station_config is validated; access fields by name
        # e.g. open serial port: serial.Serial(station_config.serial_port)
        return {}


if __name__ == '__main__':
    ExampleTester()

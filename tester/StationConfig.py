from typing import Literal

from pydantic import BaseModel, ConfigDict


class StationConfig(BaseModel):
    """Base class for per-station hardware configuration.

    Subclass this in your tester to define station-specific fields
    (e.g. serial port, IP address, calibration offsets).  The JSON
    file specified by TesterConfig.station_config_file is parsed and
    validated against your subclass before being passed to _init().

    Example::

        class MyStationConfig(StationConfig):
            serial_port: str = "COM1"
            ip_address: str = "192.168.1.100"

        cfg = TesterConfig(
            ...
            station_config_file="./station.json",
            station_config_class=MyStationConfig,
        )

    Unknown keys in the JSON file are ignored by default.

    ``ui_theme`` controls the web UI's initial light/dark mode for every
    station. Operators can still switch modes from the sidebar.
    """

    model_config = ConfigDict(extra='ignore')

    ui_theme: Literal['light', 'dark'] = 'light'

import pytest

from tester.TesterIf import TesterIf as InterfaceUnderTest


class SocketRunner:
    def __init__(self):
        self.options = None

    def run(self, app, **options):
        self.options = options


def make_interface(cert_file=None, key_file=None):
    interface = object.__new__(InterfaceUnderTest)
    interface.app = object()
    interface.sio = SocketRunner()
    interface.ssl_cert_file = cert_file
    interface.ssl_key_file = key_file
    return interface


def test_run_configures_ssl_context():
    interface = make_interface("station.crt", "station.key")

    interface.run()

    assert interface.sio.options["ssl_context"] == ("station.crt", "station.key")


def test_run_rejects_incomplete_ssl_configuration():
    interface = make_interface(cert_file="station.crt")

    with pytest.raises(ValueError, match="must be configured together"):
        interface.run()
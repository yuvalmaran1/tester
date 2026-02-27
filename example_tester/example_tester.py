from tester import Tester
from tester.TestLogger import TestLogger
from tester.TesterConfig import TesterConfig

class ExampleTester(Tester):
    def __init__(self, ui=True) -> None:
        cfg = TesterConfig(name="Example Tester",\
                           description="Production Tester", \
                           version="0.0.1", \
                           db_config="./TestDB.db", \
                           setup_file="./setup.json", \
                           duts_file="./duts.json", \
                           log_dir= None,\
                           ui=ui \
                        )

        super().__init__(cfg)

    def _init(self, setup: dict) -> dict:

        return {}


if __name__ == '__main__':
    ExampleTester()

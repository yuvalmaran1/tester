import logging
import sys
import datetime
from .Singleton import Singleton

class TestLogger(metaclass=Singleton):
    _logger = None
    _fmt = logging.Formatter('[%(asctime)s.%(msecs)03d] - %(module)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    _dirname = './logs'
    _filename = None

    def __new__(cls, *args, **kwargs):
        if cls._logger is None:
            name = kwargs.get("name", 'TestLogger')
            cls._dirname = kwargs.get("dirname", './logs')

            cls._logger = logging.Logger(name)
            cls._logger.setLevel(logging.DEBUG)
            
            sh = logging.StreamHandler(sys.stdout)
            sh.setFormatter(cls._fmt)
            cls._logger.addHandler(sh)

        return cls._logger
    
    @classmethod
    def start_run(cls, entrylist: list):
        # generate file name
        now = datetime.datetime.now()

        # add file handler if dirname is not None
        if cls._dirname:
            cls._filename = f"{cls._dirname}/log_{now.strftime('%Y_%m_%d_%H_%M_%S')}.log"
            fh = logging.FileHandler(cls._filename)
            fh.setFormatter(cls._fmt)
            cls._logger.addHandler(fh)

        # add list handler
        lh = LogListHandler(entrylist)
        lh.setFormatter(cls._fmt)
        cls._logger.addHandler(lh)
    
    @classmethod
    def stop_run(cls):
        fh = list(filter(lambda h: isinstance(h, logging.FileHandler) or isinstance(h, LogListHandler), cls._logger.handlers))
        for h in fh:
            cls._logger.removeHandler(h)

class LogListHandler(logging.StreamHandler):
    def __init__(self, entrylist: list):
        logging.StreamHandler.__init__(self)
        self.entrylist = entrylist

    def emit(self, record):
        self.entrylist.append(self.format(record) + '\n')
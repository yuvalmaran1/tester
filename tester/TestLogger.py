import logging
import sys
import datetime
from .Singleton import Singleton

class TestLogger(metaclass=Singleton):
    _fmt = logging.Formatter('[%(asctime)s.%(msecs)03d] - %(module)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    def __init__(self, name: str = 'TestLogger', dirname: str = './logs'):
        # __init__ is called every time, but Singleton.__call__ returns the existing
        # instance after the first construction, so only the first call matters.
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self._dirname = dirname
        self._logger = logging.Logger(name)
        self._logger.setLevel(logging.DEBUG)
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(self._fmt)
        self._logger.addHandler(sh)

    # Proxy methods so callers can use logger.info(...) etc. directly.
    # stacklevel=2 makes the logging machinery attribute the record to the
    # actual caller rather than this proxy, so %(module)s shows the right name.
    def debug(self, msg, *args, **kwargs):
        self._logger.debug(msg, *args, stacklevel=2, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._logger.info(msg, *args, stacklevel=2, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._logger.warning(msg, *args, stacklevel=2, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._logger.error(msg, *args, stacklevel=2, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._logger.critical(msg, *args, stacklevel=2, **kwargs)

    def addHandler(self, handler):
        self._logger.addHandler(handler)

    def removeHandler(self, handler):
        self._logger.removeHandler(handler)

    def start_run(self, entrylist: list):
        now = datetime.datetime.now()
        if self._dirname:
            filename = f"{self._dirname}/log_{now.strftime('%Y_%m_%d_%H_%M_%S')}.log"
            fh = logging.FileHandler(filename)
            fh.setFormatter(self._fmt)
            self._logger.addHandler(fh)
        lh = LogListHandler(entrylist)
        lh.setFormatter(self._fmt)
        self._logger.addHandler(lh)

    def stop_run(self):
        to_remove = [h for h in self._logger.handlers
                     if isinstance(h, (logging.FileHandler, LogListHandler))]
        for h in to_remove:
            self._logger.removeHandler(h)

class LogListHandler(logging.StreamHandler):
    def __init__(self, entrylist: list):
        logging.StreamHandler.__init__(self)
        self.entrylist = entrylist

    def emit(self, record):
        self.entrylist.append(self.format(record) + '\n')
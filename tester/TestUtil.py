from threading import Event, RLock
from enum import Enum, auto
from time import time
from .Singleton import Singleton
from .TestLogger import TestLogger

class AbortRunException(Exception):
        pass

class TestAttachment(metaclass=Singleton):
    def __init__(self):
        self.run = None
    
    def set_run(self, run):
        self.run = run

    def attach_file(self, file_path: str):
        self.run.append_attachment_file(file_path)

    def attach_buffer(self, data, file_name: str):
        self.run.append_attachment_buffer(data, file_name)

class TestDialog(metaclass=Singleton):

    class Response(Enum):
        Ok = auto()
        Cancel = auto()
        Yes = auto()
        No = auto()

    def __init__(self):
        self._lock = RLock()
        self._response_event = Event()
        self._close_on_response = True
        self.show = False
        self.title = 'untitled'
        self.text = ''
        self.responses = [TestDialog.Response.Ok]
        self.schema = {"type": "object", "properties": {}}
        self.defaults = {}
        self.timeout = 30
        self.response = None
        self.response_data = None
        self.start_time = 0
        self.progress = None

    def _open(self, title, text, schema, defaults, timeout, responses, close_on_response):
        with self._lock:
            self.title = title
            self.text = text
            self.responses = list(responses)
            self.schema = schema
            self.defaults = defaults
            self.timeout = timeout
            self.response = None
            self.response_data = None
            self.start_time = time()
            self.progress = None
            self._close_on_response = close_on_response
            self._response_event.clear()
            self.show = True
        TestLogger().debug(f'displaying dialog. title: "{self.title}". timeout: {self.timeout}sec.')

    def submit_response(self, response, response_data=None):
        """Record an operator response without necessarily hiding the dialog."""
        with self._lock:
            self.response = response
            self.response_data = response_data
            if self._close_on_response:
                self.show = False
            self._response_event.set()

    def close(self):
        """Hide the dialog and release any thread waiting for a response."""
        with self._lock:
            self.show = False
            self._response_event.set()

    def display(self, title: str = '', text: str = '', schema: dict = None,
                defaults=None, timeout=30, responses=None) -> dict:
        """Display a dialog and block until the operator responds or it times out."""
        self._open(
            title,
            text,
            schema or {"type": "object", "properties": {}},
            defaults or {},
            timeout,
            [TestDialog.Response.Ok] if responses is None else responses,
            close_on_response=True,
        )
        self._response_event.wait(None if self.timeout == 0 else self.timeout)
        TestLogger().debug(f'dialog closed. response: "{self.response}". data: {self.response_data}')
        with self._lock:
            self.show = False
        return self.response

    def display_non_blocking(self, title: str = '', text: str = '', schema: dict = None,
                             defaults=None, timeout=0, responses=None):
        """Display an interactive dialog and return immediately.

        Submitted responses leave the dialog open. Call ``wait_for_response`` or
        inspect ``response``/``response_data``, update it as work progresses, and
        call ``close`` when the workflow is complete.
        """
        self._open(
            title,
            text,
            schema or {"type": "object", "properties": {}},
            defaults or {},
            timeout,
            [TestDialog.Response.Ok] if responses is None else responses,
            close_on_response=False,
        )
        return self

    def wait_for_response(self, timeout=None, clear=True):
        """Wait for the next response while leaving a non-blocking dialog visible."""
        if not self._response_event.wait(timeout):
            return None
        with self._lock:
            response = self.response
            if clear:
                self._response_event.clear()
            return response

    def update(self, *, title=None, text=None, schema=None, defaults=None,
               responses=None, progress=None):
        """Update visible dialog content without closing or reopening it."""
        with self._lock:
            if title is not None:
                self.title = title
            if text is not None:
                self.text = text
            if schema is not None:
                self.schema = schema
            if defaults is not None:
                self.defaults = defaults
            if responses is not None:
                self.responses = list(responses)
            if progress is not None:
                self.progress = max(0, min(100, progress))

    def encode(self):
        with self._lock:
            if self.progress is not None:
                progress = self.progress
            elif self.timeout == 0:
                progress = 0
            else:
                progress = min(100, 100 * (time() - self.start_time) / self.timeout)
            return {
                "show": self.show,
                "title": self.title,
                "text": self.text,
                "responses": [r.name for r in self.responses],
                "schema": self.schema,
                "defaults": self.defaults,
                "timeout": self.timeout,
                "progress": progress,
            }
import base64
import mimetypes
import pathlib
import re
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

    _MARKDOWN_IMAGE = re.compile(r'!\[[^\]]*\]\((?:<([^>]+)>|([^\s)]+))')

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
        self.markdown = ''
        self.markdown_images = {}
        self.responses = [TestDialog.Response.Ok]
        self.schema = {"type": "object", "properties": {}}
        self.defaults = {}
        self.timeout = 30
        self.response = None
        self.response_data = None
        self.start_time = 0
        self.progress = None

    @classmethod
    def _load_markdown(cls, markdown_file):
        if markdown_file is None:
            return '', {}

        markdown_path = pathlib.Path(markdown_file).resolve()
        if markdown_path.suffix.lower() != '.md':
            raise ValueError('markdown_file must reference a .md file')

        markdown = markdown_path.read_text(encoding='utf-8')
        images = {}
        for match in cls._MARKDOWN_IMAGE.finditer(markdown):
            source = match.group(1) or match.group(2)
            if '://' in source or source.startswith(('data:', '#', '/')):
                continue

            image_path = (markdown_path.parent / source).resolve()
            mime_type, _ = mimetypes.guess_type(image_path)
            if not image_path.is_file() or not (mime_type or '').startswith('image/'):
                continue

            encoded = base64.b64encode(image_path.read_bytes()).decode('ascii')
            images[source] = f'data:{mime_type};base64,{encoded}'
        return markdown, images

    def _open(self, title, text, markdown_file, schema, defaults, timeout, responses,
              close_on_response):
        markdown, markdown_images = self._load_markdown(markdown_file)
        with self._lock:
            self.title = title
            self.text = text
            self.markdown = markdown
            self.markdown_images = markdown_images
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
                defaults=None, timeout=30, responses=None, markdown_file=None) -> dict:
        """Display a dialog and block until the operator responds or it times out."""
        self._open(
            title,
            text,
            markdown_file,
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
                             defaults=None, timeout=0, responses=None, markdown_file=None):
        """Display an interactive dialog and return immediately.

        Submitted responses leave the dialog open. Call ``wait_for_response`` or
        inspect ``response``/``response_data``, update it as work progresses, and
        call ``close`` when the workflow is complete.
        """
        self._open(
            title,
            text,
            markdown_file,
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

    def update(self, *, title=None, text=None, markdown_file=None, schema=None,
               defaults=None, responses=None, progress=None):
        """Update visible dialog content without closing or reopening it."""
        markdown = markdown_images = None
        if markdown_file is not None:
            markdown, markdown_images = self._load_markdown(markdown_file)
        with self._lock:
            if title is not None:
                self.title = title
            if text is not None:
                self.text = text
            if markdown is not None:
                self.markdown = markdown
                self.markdown_images = markdown_images
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
                "markdown": self.markdown,
                "markdown_images": self.markdown_images,
                "responses": [r.name for r in self.responses],
                "schema": self.schema,
                "defaults": self.defaults,
                "timeout": self.timeout,
                "progress": progress,
            }
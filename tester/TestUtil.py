from threading import Semaphore
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
        self.sem = Semaphore(0)
        
    def close(self, response, reponse_data):
         self.response = response
         self.response_data = reponse_data
         self.show = False
         self.sem.release()

    def display(self, title: str = '', text: str = '', 
                schema: dict = {"type": "object", "properties": {}},
                defaults = {}, timeout = 30, responses = [Response.Ok]) -> dict:
        self.title = title
        self.text = text
        self.responses = responses
        self.schema = schema
        self.defaults = defaults
        self.timeout = timeout
        self.response = None
        self.response_data = None
        self.start_time = time()
        self.show = True
        TestLogger().debug(f'displaying dialog. title: "{self.title}". timeout: {self.timeout}sec.')
        self.sem.acquire(True, self.timeout)
        TestLogger().debug(f'dialog closed. response: "{self.response}". data: {self.response_data}')
        self.show = False
        return self.response
        
    def encode(self):
         progress = 0 if self.timeout == 0 else (100 * (time() - self.start_time) / self.timeout)
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
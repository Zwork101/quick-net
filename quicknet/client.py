from threading import Thread
from traceback import print_exception
try:
    import dill as pickle
except ModuleNotFoundError:
    import pickle
import socket
import sys
from queue import Queue

from quicknet import event
from quicknet import utils

__all__ = ["QClient"]


class QClient(event.EventThreader, Thread, socket.socket):

    def __init__(self, ip: str, port: int, buffer_size: int=2047, family: int=socket.AF_INET,
                 type: int=socket.SOCK_STREAM, timeout=.5):
        Thread.__init__(self)
        event.EventThreader.__init__(self)
        socket.socket.__init__(self, family=family, type=type)

        self.buffer_size = buffer_size
        self.ip = ip
        self.port = port
        self.running = False
        self.tasks = Queue()
        self.settimeout(timeout)
        self.error_handler()

    @staticmethod
    def error_handler(callback=None):
        if callback is None:
            sys.excepthook = print_exception
        else:
            sys.excepthook = callback

    def call(self, handler: str, *args, **kwargs):
        if not self.running:
            raise utils.NotRunningError("Not connected to server")
        data = pickle.dumps((handler, args, kwargs))
        if len(data) > self.buffer_size:
            raise utils.DataOverflowError("Too much data to send ({size} > {max})"
                                          .format(size=len(data), max=self.buffer_size))
        self.sendall(data)

    def run(self):
        self.connect((self.ip, self.port))
        self.running = True
        while self.running:
            try:
                data = self.recv(self.buffer_size)
            except socket.timeout:
                data = None
            except ConnectionResetError:
                self.quit()
                self.emit(self, "SERVER_DISCONNECT", self)
                continue
            if data:
                try:
                    handler, args, kwargs = pickle.loads(data)
                except (ValueError, pickle.UnpicklingError):
                    msg = pickle.dumps(("ERROR", ["Malformed request, unable to unpickle, or to few values."], {}))
                    self.send(msg)
                else:
                    self.emit(self, handler, *args, **kwargs)

    def quit(self):
        self.running = False
        self.close()

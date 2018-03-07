from threading import Thread
try:
    import dill as pickle
except ModuleNotFoundError:
    import pickle
import socket

from quicknet import utils

__all__ = ["ClientWorker"]


class ClientWorker(Thread):

    def __init__(self, id: str, conn: socket.socket, manager):
        super().__init__(name=id)

        self.conn = conn
        self.addr = conn.getpeername()
        self.server = manager
        self.closed = False
        self.info = {}

    def send(self, data: bytes):
        if len(data) > self.server.buffer_size:
            raise utils.DataOverflowError("Too much information (max {len} bytes)".format(len=self.server.buffer_size))
        if self.closed:
            raise utils.NotRunningError("Worker is not connected to client.")
        self.conn.sendall(data)

    def run(self):
        while not self.closed:
            try:
                data = self.conn.recv(self.server.buffer_size)
            except (ConnectionResetError, ConnectionAbortedError):
                self.kill()
                continue
            if data:
                try:
                    handler, args, kwargs = pickle.loads(data)
                except (ValueError, pickle.UnpicklingError):
                    self.emit("ERROR", "Malformed request, unable to unpickle, or to few values.")
                else:
                    self.server.emit(self, handler, *args, **kwargs)

    def emit(self, handler, *args, **kwargs):
        cmd = pickle.dumps((handler, args, kwargs))
        self.send(cmd)

    def kill(self):
        if self.closed:
            raise utils.NotRunningError("Connection not made, can't kill non-existent connection.")
        self.conn.close()
        self.closed = True
        self.server.emit(self, "CLIENT_DISCONNECT", self)

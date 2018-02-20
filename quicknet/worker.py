from threading import Thread
import pickle
import socket

from quicknet import utils

__all__ = ["ClientWorker"]


class ClientWorker(Thread):

    def __init__(self, id: str, conn: socket.socket, manager):
        super().__init__(name=id)

        self.conn = conn
        self.server = manager
        self.closed = False

    def send(self, data: bytes):
        if len(data) > self.server.buffer_size:
            raise utils.DataOverflowError("Too much information (max {} bytes".format(self.server.buffer_size))
        if self.closed:
            raise utils.NotRunningError("Worker is not connected to client.")
        self.conn.sendall(data)

    def run(self):
        while not self.closed:
            try:
                data = self.conn.recv(self.server.buffer_size)
            except ConnectionResetError:
                self.kill()
                self.server.emit(self, "CLIENT_DISCONNECT", self)
                continue
            if data:
                try:
                    handler, args, kwargs = pickle.loads(data)
                except (ValueError, pickle.UnpicklingError):
                    msg = pickle.dumps(("ERROR", ["Malformed request, unable to unpickle, or to few values."], {}))
                    self.send(msg)
                else:
                    self.server.emit(self, handler, *args, **kwargs)

    def emit(self, handler, *args, **kwargs):
        cmd = pickle.dumps((handler, args, kwargs))
        self.send(cmd)

    def kill(self):
        self.conn.close()
        self.closed = True

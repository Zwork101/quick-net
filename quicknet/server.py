from traceback import print_exception
import sys
import socket
from queue import Queue
from uuid import uuid4

from quicknet import event
from quicknet import utils
from quicknet import worker

__all__ = ['QServer']


class QServer(event.EventThreader, socket.socket):

    def __init__(self, port: int, local_only: bool=False, buffer_size: int=2047,
                 family: int=socket.AF_INET, type: int=socket.SOCK_STREAM):

        socket.socket.__init__(self, family, type)
        event.EventThreader.__init__(self)

        self.local = local_only
        self.port = port
        self.running = True
        self.buffer_size = buffer_size
        self.clients = {}
        self.queues = {}
        self.error_handler()

    @staticmethod
    def error_handler(callback=None):
        if callback is None:
            sys.excepthook = print_exception
        else:
            sys.excepthook = callback

    def quit(self):
        if not self.running:
            raise utils.NotRunningError("The server hasn't been started yet.")

        self.running = False
        for client in self.clients.values():
            client.kill()
        self.close()

    def run(self, max=50):
        if self.local:
            self.bind(('127.0.0.1', self.port))
        else:
            self.bind(('0.0.0.0', self.port))

        self.running = True
        self.listen(max)

        while self.running:
            conn, addr = self.accept()
            if conn.getsockname() not in [c.conn.getsockname() for c in self.clients.values()]:
                id = str(uuid4())
                client = worker.ClientWorker(id, conn, self)
                self.clients[id] = client
                self.queues[id] = Queue()
                client.start()
                self.emit(client, 'CONNECTION', conn, addr)
            else:
                # Ug, already have worker as a variable :p
                employee = [c for c in self.clients.values() if c.conn.getsockname() == conn.getsockname()][0]
                employee.closed = False
                employee.conn = conn
                if not employee.is_alive():
                    client = worker.ClientWorker(employee.name, employee.conn, self)
                    self.clients[client.name] = client
                    client.start()

    def broadcast(self, handler: str, *args, **kwargs):
        for queue in self.queues.values():
            queue.put((handler, args, kwargs))

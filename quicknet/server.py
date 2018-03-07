from traceback import print_exception
from threading import Thread
import sys
import socket
from uuid import uuid4

from quicknet import event
from quicknet import utils
from quicknet import worker

__all__ = ['QServer']


class QServer(event.EventThreader, socket.socket, Thread):

    def __init__(self, port: int, local_only: bool=False, buffer_size: int=2047,
                 family: int=socket.AF_INET, type: int=socket.SOCK_STREAM):

        socket.socket.__init__(self, family, type)
        event.EventThreader.__init__(self)
        Thread.__init__(self)

        self.local = local_only
        self.port = port
        self.running = True
        self.buffer_size = buffer_size
        self.clients = {}
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
            try:
                conn, addr = self.accept()
            except OSError:
                continue
            if conn.getpeername()[0] not in [c.addr[0] for c in self.clients.values()]:
                id = str(uuid4())
                client = worker.ClientWorker(id, conn, self)
                self.clients[id] = client
                client.start()
                self.emit(client, 'CONNECTION', conn, addr)
            else:
                # Ug, already have worker as a variable :p
                employee = [c for c in self.clients.values() if c.addr[0] == conn.getpeername()[0]][0]
                if employee.is_alive():
                    employee.kill()
                client = worker.ClientWorker(employee.name, conn, self)
                client.info = employee.info.copy()
                self.clients[client.name] = client
                client.start()
                self.emit(client, 'CONNECTION_RESET', conn, addr)

    def broadcast(self, handler: str, *args, **kwargs):
        for client in self.clients.values():
            if not client.closed:
                client.emit(handler, *args, **kwargs)

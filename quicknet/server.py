from traceback import print_exception
from threading import Thread
import ssl
import sys
import socket
from uuid import uuid4

from quicknet import event
from quicknet import utils
from quicknet import worker

__all__ = ['QServer']


class QServer(event.EventThreader, Thread):

    def __init__(self, port: int, local_only: bool=False, buffer_size: int=2047, family: int=socket.AF_INET,
                 type: int=socket.SOCK_STREAM, use_ssl: bool=False, ssl_data: dict=None):

        event.EventThreader.__init__(self)
        Thread.__init__(self)

        self.sock = socket.socket(family, type)
        self.local = local_only
        self.port = port
        self.running = True
        self.buffer_size = buffer_size
        self.clients = {}
        self.error_handler()
        self.ssl = use_ssl

        if use_ssl:
            if ssl_data is None:
                ssl_data = {}
            self.sock = ssl.wrap_socket(self.sock, ssl_data.get('keyfile'), ssl_data.get('certfile'), True,
                                        ssl_data.get('cert_reqs', ssl.CERT_NONE),
                                        ssl_data.get('ssl_version', ssl.PROTOCOL_SSLv23), ssl_data.get('ca_certs'),
                                        ssl_data.get('do_handshake_on_connect', True),
                                        ssl_data.get('suppress_ragged_eofs', True), ssl_data.get('ciphers'))

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
        self.sock.close()

    def run(self, max=50):
        if self.local:
            self.sock.bind(('127.0.0.1', self.port))
        else:
            self.sock.bind(('0.0.0.0', self.port))

        self.running = True
        self.sock.listen(max)

        while self.running:
            try:
                conn, addr = self.sock.accept()
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

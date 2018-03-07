from threading import Thread
from traceback import print_exception
try:
    import dill as pickle
except ModuleNotFoundError:
    import pickle
import ssl
import socket
import sys
from queue import Queue

from quicknet import event
from quicknet import utils

__all__ = ["QClient"]


class QClient(event.EventThreader, Thread):

    def __init__(self, ip: str, port: int, buffer_size: int=2047, family: int=socket.AF_INET,
                 type: int=socket.SOCK_STREAM, use_ssl: bool=False, ssl_data: dict={}):
        Thread.__init__(self)
        event.EventThreader.__init__(self)

        self.sock = socket.socket(family=family, type=type)
        self.buffer_size = buffer_size
        self.ip = ip
        self.port = port
        self.running = False
        self.tasks = Queue()
        self.error_handler()
        self.ssl = use_ssl

        if use_ssl:
            if ssl_data is None:
                ssl_data = {}
            self.sock = ssl.wrap_socket(self.sock, ssl_data.get('keyfile'), ssl_data.get('certfile'), False,
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

    def call(self, handler: str, *args, **kwargs):
        if not self.running:
            raise utils.NotRunningError("Not connected to server")
        data = pickle.dumps((handler, args, kwargs))
        if len(data) > self.buffer_size:
            raise utils.DataOverflowError("Too much data to send ({size} > {max})"
                                          .format(size=len(data), max=self.buffer_size))
        self.sock.sendall(data)

    def run(self):
        self.sock.connect((self.ip, self.port))
        self.running = True
        while self.running:
            try:
                data = self.sock.recv(self.buffer_size)
            except ConnectionResetError:
                self.quit()
                self.emit(self, "SERVER_DISCONNECT", self)
                continue
            if data:
                try:
                    handler, args, kwargs = pickle.loads(data)
                except (ValueError, pickle.UnpicklingError):
                    msg = pickle.dumps(("ERROR", ["Malformed request, unable to unpickle, or to few values."], {}))
                    self.sock.send(msg)
                else:
                    self.emit(self, handler, *args, **kwargs)

    def quit(self):
        self.running = False
        self.sock.close()

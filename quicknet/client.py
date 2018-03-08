import logging as log
from threading import Thread
from traceback import print_exception
import ssl
import socket
import sys
from queue import Queue

from quicknet import event, utils, sterilizer

__all__ = ["QClient"]


class QClient(event.EventThreader, Thread):

    def __init__(self, ip: str, port: int, buffer_size: int=2047, family: int=socket.AF_INET,
                 type: int=socket.SOCK_STREAM, use_ssl: bool=False, ssl_data: dict=None):
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
            log.debug("Added SSL to QClient instance.")
        log.debug("QClient instance finished initialization.")

    @staticmethod
    def error_handler(callback=None):
        if callback is None:
            sys.excepthook = print_exception
        else:
            sys.excepthook = callback
        log.info("Exception hook changed to: {handler}.".format(handler=sys.excepthook))

    def call(self, handler: str, *args, **kwargs):
        if not self.running:
            log.warning("QClient instance isn't connected to the server, unable to send data.")
            raise utils.NotRunningError("Not connected to server")
        data = sterilizer.dirty((handler, args, kwargs))
        if len(data) > self.buffer_size:
            log.warning(
                "Unable to send data, to many bytes ({size} > {max})".format(size=len(data), max=self.buffer_size))
            raise utils.DataOverflowError("Too much data to send ({size} > {max})"
                                          .format(size=len(data), max=self.buffer_size))
        self.sock.sendall(data.encode())
        log.debug("Information sent to server, {len} bytes.".format(len=len(data)))

    def run(self):
        self.sock.connect((self.ip, self.port))
        self.running = True
        log.info("Starting connection loop (connected to server)")
        while self.running:
            try:
                data = self.sock.recv(self.buffer_size).decode()
            except ConnectionResetError:
                self.quit()
                log.info("Server disconnected, ending loop.")
                self.emit(self, "SERVER_DISCONNECT", self)
                continue
            if data:
                try:
                    handler, args, kwargs = sterilizer.clean(data)
                except (ValueError, utils.BadSterilization):
                    log.info("Server sent us a malformed call.")
                    self.emit(self, "BAD_CALL", data)
                    msg = sterilizer.dirty(("ERROR", ["Malformed request, unable to unpickle, or to few values."], {}))
                    self.sock.send(msg.encode())
                else:
                    log.debug("Received data from server, {len} bytes.".format(len=len(data)))
                    self.emit(self, handler, *args, **kwargs)

    def quit(self):
        self.running = False
        self.sock.close()
        log.info("Client has been stopped.")

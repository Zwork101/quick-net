import logging as log
from time import time
from threading import Thread
from traceback import print_exception
import ssl
import socket
import sys

from quicknet import event, utils, sterilizer

__all__ = ["QClient"]


class QClient(event.EventThreader, Thread):

    EVENTS = 'SERVER_DISCONNECTED',

    def __init__(self, ip: str, port: int, buffer_size: int=2047, family: int=socket.AF_INET,
                 type: int=socket.SOCK_STREAM, use_ssl: bool=False, ssl_data: dict=None, timeout: int=2):
        Thread.__init__(self)
        event.EventThreader.__init__(self)

        self.sock = socket.socket(family=family, type=type)  # type: socket.socket
        self.buffer_size = buffer_size                       # type: int
        self.ip = ip                                         # type: str
        self.port = port                                     # type: int
        self.running = False                                 # type: bool
        self.ssl = use_ssl                                   # type: bool
        self._reqs = {}                                      # type: dict
        self.timeout = timeout                               # type: int
        self.error_handler()

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

    def __getitem__(self, item):
        self._reqs[('GET', item)] = '__waiting'
        self.send(sterilizer.dirty(['GET', item]))
        start = time()
        while self._reqs[('GET', item)] == '__waiting':
            if self.timeout is not None:
                if time() - start > self.timeout:
                    raise TimeoutError("Server took to long to respond")
        return self._reqs[('GET', item)]

    def __setitem__(self, key, value):
        req = sterilizer.dirty(['SET', key, value])
        self.send(req)

    def __delitem__(self, key):
        req = sterilizer.dirty(['DEL', key])
        self.send(req)

    @staticmethod
    def error_handler(callback=None):
        if callback is None:
            sys.excepthook = print_exception
        else:
            sys.excepthook = callback
        log.info("Exception hook changed to: {handler}.".format(handler=sys.excepthook))

    def call(self, handler: str, *args, **kwargs):
        data = sterilizer.dirty((handler, args, kwargs))
        self.send(data)

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
                    info = sterilizer.clean(data)
                except utils.BadSterilization:
                    log.info("Server sent us a malformed call.")
                    self.call("BAD_CALL", data)
                else:
                    log.debug("Received data from server, {len} bytes.".format(len=len(data)))
                    if type(info) == tuple:
                        if len(info) < 3 or len(info) > 3:
                            log.info("Server sent us either to much or too little information.")
                            self.call("BAD_CALL", info)
                        elif info[0] in self.EVENTS:
                            log.info("Server sent event ({e}) only triggerable by client side.".format(e=info[0]))
                            self.call("BAD_CALL", info)
                        else:
                            handler, args, kwargs = info
                            self.emit(self, handler, *args, **kwargs)
                    elif type(info) == list:
                        if info[0] == 'FOUND':
                            self._reqs[('GET', info[1])] = info[2]
                            log.debug("Server said shared data {key} was {val}".format(key=info[1], val=info[2]))
                        elif info[0] == 'CHANGED':
                            log.debug("Server set shared data {key} to {val}".format(key=info[1], val=info[2]))
                        elif info[0] == 'REMOVED':
                            log.debug("Server deleted shared data {key}".format(key=info[1]))
                        else:
                            log.info("Server sent us invalid information")
                            self.emit("BAD_CALL", info)
                    else:
                        log.info("Server sent us unrecognized information")
                        self.emit("BAD_CALL", info)

    def quit(self):
        self.running = False
        self.sock.close()
        log.info("Client has been stopped.")

    def send(self, data: str or bytes):
        if not self.running:
            log.warning("QClient instance isn't connected to the server, unable to send data.")
            raise utils.NotRunningError("Not connected to server")
        if len(data) > self.buffer_size:
            log.warning(
                "Unable to send data, to many bytes ({size} > {max})".format(size=len(data), max=self.buffer_size))
            raise utils.DataOverflowError("Too much data to send ({size} > {max})"
                                          .format(size=len(data), max=self.buffer_size))
        if type(data) == str:
            data = data.encode()
        self.sock.sendall(data)
        log.debug("Sent data to server ({len} bytes)".format(len=len(data)))

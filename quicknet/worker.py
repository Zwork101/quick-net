import logging as log
from threading import Thread
import socket

from quicknet import utils, sterilizer

__all__ = ["ClientWorker"]


class ClientWorker(Thread):

    def __init__(self, id: str, conn: socket.socket, manager):
        super().__init__(name=id)

        self.conn = conn
        self.addr = conn.getpeername()
        self.server = manager
        self.closed = False
        self.info = {}
        log.debug("Finished ClientWorker initialization.")

    def __repr__(self):
        return "<{addr}:{conn} [{closed}]>".format(addr=self.addr, conn=self.conn,
                                                   closed="Closed" if self.closed else "Open")

    def send(self, data: bytes or str):
        if len(data) > self.server.buffer_size:
            log.warning(
                "Can't send information, too much ({len} > {max})".format(len=len(data), max=self.server.buffer_size))
            raise utils.DataOverflowError("Too much information (max {len} bytes)".format(len=self.server.buffer_size))
        if self.closed:
            log.warning("Can't send data, Worker not connected to client.")
            raise utils.NotRunningError("Worker is not connected to client.")
        self.conn.sendall(data.encode() if isinstance(data, str) else data)
        log.debug("Data sent to client, {len} bytes".format(len=len(data)))

    def run(self):
        log.info("Worker loop started, looking for data.")
        while not self.closed:
            try:
                data = self.conn.recv(self.server.buffer_size).decode()
            except (ConnectionResetError, ConnectionAbortedError):
                log.info("Client disconnected from server")
                self.kill()
                self.server.emit(self, "CLIENT_DISCONNECT", self)
                continue
            if data:
                try:
                    handler, args, kwargs = sterilizer.clean(data)
                except (ValueError, utils.BadSterilization):
                    log.info("Client sent us a malformed call.")
                    self.server.emit(self, "BAD_CALL", data)
                    self.emit("ERROR", "Malformed request, unable to unpickle, or to few values.")
                else:
                    log.debug("Received data from client, {len} bytes.".format(len=len(data)))
                    self.server.emit(self, handler, *args, **kwargs)

    def emit(self, handler, *args, **kwargs):
        cmd = sterilizer.dirty((handler, args, kwargs))
        self.send(cmd)

    def kill(self):
        if self.closed:
            log.warning("ClientWorker not connected to client, hence it can't die.")
            raise utils.NotRunningError("Connection not made, can't kill non-existent connection.")
        self.conn.close()
        self.closed = True
        self.server.emit(self, "CLIENT_DISCONNECT", self)
        log.info("{this} has stopped".format(this=self))

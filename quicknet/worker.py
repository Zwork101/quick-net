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
        self.shared = {}
        self._lock_sharing = [False]
        self._last_transmissions = []
        log.debug("Finished ClientWorker initialization.")

    def __repr__(self):
        return "<{addr}:{conn} [{closed}]>".format(addr=self.addr, conn=self.conn,
                                                   closed="Closed" if self.closed else "Open")

    @property
    def lock_sharing(self):
        return self._lock_sharing[0]

    @lock_sharing.setter
    def lock_sharing(self, val: bool):
        self._lock_sharing[0] = val

    def send(self, data: bytes or str):
        data = data if type(data) is bytes else data.encode()

        if self.server.buffer_size is not None and len(data) > self.server.buffer_size:
            log.warning(
                "Can't send information, too much ({len} > {max})".format(len=len(data), max=self.server.buffer_size))
            raise utils.DataOverflowError("Too much information (max {len} bytes)".format(len=self.server.buffer_size))
        if self.closed:
            log.warning("Can't send data, Worker not connected to client.")
            raise utils.NotRunningError("Worker is not connected to client.")

        data = b"<" + data + b">"
        while len(data) > self.server.DEFAULT_READ_SIZE:
            to_send = data[:self.server.DEFAULT_READ_SIZE]
            self.conn.sendall(to_send)
            data = data[self.server.DEFAULT_READ_SIZE:]

        self.conn.sendall(data)
        log.debug("Data sent to client, {len} bytes".format(len=len(data)))

    def run(self):
        log.info("Worker loop started, looking for data.")
        while not self.closed:
            try:
                data = self.conn.recv(self.server.buffer_size if self.server.buffer_size else 2048)
            except ConnectionResetError:
                log.info("Client Disconnected (addr {addr})".format(addr=self.addr))
                self.kill()
                continue
            try:
                if data.startswith(b"<") and self._last_transmissions:
                    log.info("Client sent new data before finishing old data.")
                    self.emit("ERROR", "data interrupted, end signal never received")
                    self._last_transmissions.clear()
                if self._last_transmissions:
                    if data.endswith(b">"):
                        data = b"".join(self._last_transmissions) + data[:len(data) - 1]
                        self._last_transmissions.clear()
                    else:
                        self._last_transmissions.append(data)
                        continue
                elif data.startswith(b"<"):
                    if data.endswith(b">"):
                        data = data[1:len(data) - 1]
                    else:
                        self._last_transmissions.append(data[1:])
                        continue
                else:
                    log.info("Information sent without start / end signals")
                    self.emit("ERROR", "Information sent without start / end signals")
                info = sterilizer.clean(data.decode())
            except utils.BadSterilization:
                log.info("Client sent us a malformed call.")
                self.emit("BAD_CALL", data)
            else:
                log.debug("Received data from client, {len} bytes.".format(len=len(data)))
                if type(info) == tuple:
                    if len(info) < 3 or len(info) > 3:
                        log.info("Client sent us either to much or too little information.")
                        self.emit("BAD_CALL", info)
                    elif info[0] in self.server.EVENTS:
                        log.info("Client sent event ({e}) only triggerable server side.".format(e=info[0]))
                        self.emit("BAD_CALL", info)
                    else:
                        handler, args, kwargs = info
                        self.server.emit(self, handler, *args, **kwargs)
                elif type(info) == list:
                    self.server.emit(self, "SERVER_REQUEST", info)
                    try:
                        if info[0] == 'GET':
                            log.debug("Client asked for value of {key}.".format(key=info[1]))
                            resp = sterilizer.dirty(['FOUND', info[1], self.shared.get(info[1])])
                            self.send(resp)
                        elif info[0] == 'SET':
                            if not self.lock_sharing:
                                self.shared[info[1]] = info[2]
                                resp = sterilizer.dirty(['CHANGED', info[1], info[2]])
                                self.send(resp)
                                log.debug("Client set shared data {key} to {val}".format(key=info[1], val=info[2]))
                        elif info[0] == 'DEL':
                            if info[1] in self.shared and not self.lock_sharing:
                                del self.shared[info[1]]
                                resp = sterilizer.dirty(['REMOVED', info[1]])
                                self.send(resp)
                                log.debug("Client deleted shared data {key}".format(key=info[1]))
                        else:
                            log.info("Client sent us invalid information")
                            self.emit("BAD_CALL", info)
                    except IndexError:
                        log.info("Client sent us either to much or too little information.")
                        self.emit("BAD_CALL", info)
                else:
                    log.info("Client sent us unrecognized information")
                    self.emit("BAD_CALL", info)

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

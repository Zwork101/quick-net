import logging

from quicknet.server import QServer
from quicknet.event import ClientWorker

# Add LOGGING! Yes, this library has logging.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('MyServerLogger')
# Change use_ssl to True, to activate ssl's TRUE POWER (client must have ssl enabled too)
server = QServer(5421, use_ssl=True, ssl_data={'keyfile': 'selfsigned.key', 'certfile': 'selfsigned.crt'})
users = {}


@server.on("CONNECTION")
def new_player(_, address):
    print("New connection!", address)
    ClientWorker.lock_sharing = True
    # That is True if we don't want the client to make changes, otherwise the default is False
    ClientWorker.emit("WELCOME", "Welcome player! Please send your name & pass.")


@server.on("NAME", enforce_annotations=True)
def set_name(name: str, password: str):
    ClientWorker.info[name] = password
    ClientWorker.shared['name'] = name


@server.on("MSG", enforce_annotations=True)
def new_message(msg: str):
    print("New Message! ({name})".format(name=ClientWorker.shared['name']), msg)
    server.broadcast("NEW_MSG", msg, ClientWorker.shared['name'])


@server.on("ERROR")
def error(msg):
    print(msg)


print("Starting Program")
server.start()
input()
server.quit()

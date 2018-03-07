from quicknet.server import QServer
from quicknet.event import ClientWorker

# Change use_ssl to True, to activate ssl's TRUE POWER (client must have ssl enabled too)
server = QServer(5421, use_ssl=False, ssl_data={'keyfile': 'selfsigned.key', 'certfile': 'selfsigned.crt'})

users = {}


@server.on("CONNECTION")
def new_player(_, address):
    print("New connection!", address)
    ClientWorker.emit("WELCOME", "Welcome player! Please send your name & pass.")


@server.on("NAME")
def set_name(name, password):
    other_ip = ClientWorker.conn.getpeername()
    if other_ip in users:
        if (name, password) != users[other_ip]:
            ClientWorker.emit("ERROR", "Invalid name or password")
    else:
        users[other_ip] = (name, password)


@server.on("MSG")
def new_message(msg):
    print("New Message!", msg)
    if ClientWorker.conn.getpeername() in users:
        name = users[ClientWorker.conn.getpeername()][0]
        server.broadcast("NEW_MSG", msg, name)


@server.on("ERROR")
def error(msg):
    print(msg)


print("Starting Program")
server.start()
input()
server.quit()

from quicknet.server import QServer

server = QServer(5421)

users = {}


@server.on("CONNECTION", pass_client=True)
def new_player(worker, _, address):
    print("New connection!", address)
    worker.emit("WELCOME", "Welcome player! Please send your name & pass.")


@server.on("NAME", pass_client=True)
def set_name(client, name, password):
    other_ip = client.conn.getpeername()
    if other_ip in users:
        if (name, password) != users[other_ip]:
            client.emit("ERROR", "Invalid name or password")
    else:
        users[other_ip] = (name, password)


@server.on("MSG", pass_client=True)
def new_message(client, msg):
    print("New Message!", msg)
    if client.conn.getpeername() in users:
        name = users[client.conn.getpeername()][0]
        server.broadcast("NEW_MSG", msg, name)


@server.on("ERROR")
def error(msg):
    print(msg)


print("Starting Program")
server.run()

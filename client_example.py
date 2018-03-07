from time import sleep

from quicknet.client import QClient

# Change use_ssl to True, to activate ssl's TRUE POWER (server must have ssl enabled too)
client = QClient("127.0.0.1", 5421, use_ssl=False)
logged_in = False
username = None
password = None
messages = ("Hello dude!", "How are you?", "I'm great, thanks", "this could be a much better example than it is.")


@client.on("ERROR")
def error(err):
    print(err)


@client.on("WELCOME")
def show_ask(welcome):
    global username, password, logged_in
    print(welcome)
    username = input("Username: ")
    password = input("Password: ")
    client.call("NAME", username, password)
    logged_in = True


@client.on("NEW_MSG")
def new_msg(msg, name):
    if name != username:
        print(name, ":", msg)
    else:
        print("You:", msg)


client.start()

while not logged_in:
    sleep(.2)

for msg in messages:
    sleep(1)
    client.call("MSG", msg)

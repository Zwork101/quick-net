import logging
from time import sleep
from os import urandom

from quicknet.client import QClient

# Add LOGGING! Yes, this library has logging.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('MyServerLogger')
# Change use_ssl to True, to activate ssl's TRUE POWER (server must have ssl enabled too)
client = QClient("127.0.0.1", 5421, use_ssl=True)
messages = ("Hello dude!", "How are you?", "I'm great, thanks",
            "this could be a much better example than it is.", 5, str(urandom(4000)))
# The server is using check_annotations
# The urandom is to show off, that there is no size limit to data. That sends more then 4000 bytes


def main():
    for msg in messages:
        sleep(1)
        client.call("MSG", msg)


@client.on("WELCOME")
def show_ask(welcome):
    global username, password
    print(welcome)
    username = input("Username: ")
    password = input("Password: ")
    client.call("NAME", username, password)
    # client['name'] = "MR. COOLIO"
    # Only works if shared information isn't locked
    main()


@client.on("NEW_MSG")
def new_msg(msg, name):
    if name != client['name']:  # This is a shared variable, set by the server!
        print(name, ":", msg)
    else:
        print("You:", msg)


@client.on("ERROR")
def error(issue: str):
    print(issue)


client.start()

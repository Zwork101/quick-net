# quick-net
## Sockets don't have to be a pain

That's the motto this library was built with, and that's exactly what we made! This is a top-level socket library,
great for games, chat, or anything networking in general!

# How to install
As of now, this repo doesn't have a setup.py (which will be added later), however it's easy enough
to make one yourself. But to make it easy, it's also on *pip*
```py3
pip install quick-connect  # pip3 on linux machines.
```
And please, don't get confused by the installation name, you import it as so:
```py3
import quicknet
```

# How to use
quick-connect is event based. That means, you can register handlers for when you receive a certain input. For
example, let's say I wanted my client, to print the welcome message from the server. I might do something like
this in my client program:
```py3
@client.on("WELCOME")
def welcome_msg(message):
    print("SERVER:", message)
```
The first line, basicly adds the function to the client, so the client can run it when it receives that event
from the server. The second line declares the function, which accepts a message (possitional arguemnt) from 
the server. The last line prints it out. Now, on the server side, how might we invoke this? Well, we have 2 ways,
the first way, is to get the client object, and emit that message to it.
```py3
joined_client.emit("WELCOME", "Welcome to my awesome game!")
```
However, let's say you wanted to tell *every* client, a player joined. Then you can use the broadcast function.
```py3
server.broadcast("WELCOME", "Player {name} just joined the party!".format(name="Joe"))
```

# Docs
See the github wiki on this repo for the docs, which has the API, and more details, such as how to communicate 
to a server using quick-connect, without quick-connect.

# Design
![flowchart](https://docs.google.com/drawings/d/e/2PACX-1vTMsSmu-2IDhVvM8MiY8gEsLtPd0xJmcuVLfMLF-wnhtuf-X27012i5QhtI2lOFLj1qn6BLnvtr1ViY/pub?w=960&amp;h=720)
Enough said.

# Credits
This was made by Nathan Zilora, also on discord known as `Zwack010#5682`
This project is registered in the MIT licesnse, so make sure to include
the license, if using this project directly.

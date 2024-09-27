import socket
import select
import datetime
import re

# Class that represents chat channels
class Channel:
    def __init__(self, name):
        self.name = name
        self.clients = set()

    # Adds client to channel
    def add_client(self, client):
        self.clients.add(client)

    # Removes client from channel
    def remove_client(self, client):
        self.clients.remove(client)
        
    # Function that handles delivering message to clients in the same channel
    def broadcast(self, message, sender=None):
        for client in self.clients:
            if client != sender:
                client.send_message(message)

class Client:
    # Initialize the client
    def __init__(self, socket, address):
        self.socket = socket
        self.address = address
        self.nickname = None
        self.channels = set()
        self.buffer = ""

    # Send a message to the client
    def send_message(self, message):
        self.socket.send((message + "\r\n").encode('utf-8'))

    # Handles client joining a channel in the server
    def join_channel(self, channel):
        self.channels.add(channel)
        channel.add_client(self)

     # Handles client leaving a channel in the server
    def leave_channel(self, channel):
        self.channels.remove(channel)
        channel.remove_client(self)

class Server:
    # Initialize the server
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.clients = {}
        self.channels = {}

        self.command_handlers = {
            "NICK": self.handle_nick,
            "USER": self.handle_user,
            "JOIN": self.handle_join,
            "PRIVMSG": self.handle_privmsg,
            "QUIT": self.handle_quit,
            "PING": self.handle_ping
        }

    # Start the server
    def start(self):
        self.socket.bind((self.host, self.port, 0, 0))
        self.socket.listen(5)
        print("IRC Server running on port", self.port)
        
        while True:
            try:
                # Use select to monitor the socket 
                # Timeout is set to 1 second to regularly check for new clients
                readable, _, _ = select.select([self.socket] + list(self.clients.keys()), [], [], 1)
                for sock in readable:
                    if sock == self.socket:
                        client_socket, address = self.socket.accept()
                        client = Client(client_socket, address)
                        self.clients[client_socket] = client
                        print("New connection from", address)
                    else:
                        self.handle_client(self.clients[sock])
            except Exception as e:
                print("Error:", e)

    # Handle the client
    def handle_client(self, client):
        try:
            data = client.socket.recv(2048).decode("utf-8", errors="ignore")
            if not data:
                self.remove_client(client)
            else:
                client.buffer += data
                while "\r\n" in client.buffer:
                    line, client.buffer = client.buffer.split("\r\n", 1)
                    print(f"[{client.address[0]}:{client.address[1]}] → b'{line}\r\n'")
                    self.handle_command(client, line.strip())
        except Exception as e:
            print("Error handling client", client.address, ":", e)
            self.remove_client(client)

    # Remove the client from the server
    def remove_client(self, client):
        for channel in list(client.channels):
            client.leave_channel(channel)
        del self.clients[client.socket]
        client.socket.close()
        print("Client", client.address, "disconnected")
    
    # Handle the command
    def handle_command(self, client, data):
        parts = data.split()
        if not parts:
            return
        command = parts[0].upper()

        if command in self.command_handlers:
            self.command_handlers[command](client, parts)
        else:
            client.send_message("421 * " + command + " :Unknown command")

    # Handle NICK command
    def handle_nick(self, client, parts):
        if len(parts) < 2:
            client.send_message("461 * NICK :Not enough parameters")
        else:
            new_nick = parts[1].strip()
            # Check if the nickname is valid
            if not re.match(r'^[a-zA-Z][a-zA-Z0-9\-_]*$', new_nick):
                client.send_message(f"432 * {new_nick} :Erroneous nickname")
                client.send_message("NOTICE * :Nickname must start with a letter and can contain only letters, numbers, hyphens, and underscores")
                return

            for c in self.clients.values():
                if c.nickname == new_nick:
                    client.send_message("433 * " + new_nick + " :Nickname is already in use")
                    return
                
            if client.nickname:
                for channel in client.channels:
                    # Notify other clients in the channel (we need to broadcast so that HexChat updates the nick)
                    channel.broadcast(":" + client.nickname + "!" + client.nickname + "@" + client.address[0] + " NICK :" + new_nick)
            client.nickname = new_nick

    # Handle USER command
    def handle_user(self, client, parts):
        if len(parts) < 5:
            client.send_message("461 * USER :Not enough parameters")
        else:
            client.send_message(": 001 " + client.nickname + " :Welcome to the IRC Network")
            # MOTD File is missing means there is no message to display
            client.send_message(": 422 " + client.nickname + " :MOTD File is missing")

    # Log the user's status
    def handle_log(self, status, nick, time):
        logMsg = f"User {nick} {status} at {time}\n"
        print(logMsg)
        # Write the log message to a file
        with open("log.txt", "a") as log:
            log.write(logMsg)

    # Handle JOIN command
    def handle_join(self, client, parts):
        if len(parts) < 2:
            client.send_message(": 461 * JOIN :Not enough parameters")
        else:
            channel_name = parts[1]
            if channel_name not in self.channels:
                self.channels[channel_name] = Channel(channel_name)
            channel = self.channels[channel_name]
            client.join_channel(channel)
            # Notify other clients in the channel
            channel.broadcast(":" + client.nickname + "!" + client.nickname + "@" + client.address[0] + " JOIN " + channel_name)
            # Send the client the list of users in the channel
            client.send_message(": 353 " + client.nickname + " = " + channel_name + " :" + " ".join([c.nickname for c in channel.clients]))
            time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.handle_log("connected", client.nickname, time)

    # Handle PRIVMSG command
    def handle_privmsg(self, client, parts):
        if len(parts) < 3:
            client.send_message(": 461 * PRIVMSG :Not enough parameters")
        else:
            target = parts[1]
            message = " ".join(parts[2:])[1:]
            if target.startswith("#"):
                if target in self.channels:
                    channel = self.channels[target]
                    channel.broadcast(":" + client.nickname + "!" + client.nickname + "@" + client.address[0] + " PRIVMSG " + target + " :" + message, client)
            else:
                target_client = None
                for c in self.clients.values():
                    if c.nickname == target:
                        target_client = c
                        break
                if target_client:
                    target_client.send_message(":" + client.nickname + "!" + client.nickname + "@" + client.address[0] + " PRIVMSG " + target + " :" + message)

    # Handle QUIT command
    def handle_quit(self, client, parts):
        quit_message = "Client quit"
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.handle_log("disconnected", client.nickname,time)
        if len(parts) > 1:
            quit_message = " ".join(parts[1:])[1:]
        for channel in list(client.channels):
            channel.broadcast(": " + client.nickname + "!" + client.nickname + "@" + client.address[0] + " QUIT :" + quit_message)
            client.leave_channel(channel)
        self.remove_client(client)

    # Handle PING command
    def handle_ping(self, client, parts):
        if len(parts) < 2:
            client.send_message("461 * PING :Not enough parameters")
        else:
            client.send_message(": PONG :" + parts[1])

def main():
    SERVER = "::1"
    PORT = 6667
    server = Server(SERVER, PORT)
    server.start()

if __name__ == "__main__":
    main()

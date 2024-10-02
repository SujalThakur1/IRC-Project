import socket
import select
import datetime
import re
from channel import Channel
from client import Client



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
            "CAP" : self.handle_cap,
            "QUIT": self.handle_quit,
            "PING": self.handle_ping
        }

    # Start the server
    def start(self):
        try:
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
                # ConnectionError is for connection-related issues
                # BrokenPipeError is for trying to write on a socket which has been shutdown for writing
                except(ConnectionError, BrokenPipeError):
                    print("Error: A client has disconnected")
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
            print(f"[{client.address[0]}:{client.address[1]}] → Error 421: Unkown command\r\n")


    def handle_cap(self, client, parts):
        print(f"[{client.address[0]}:{client.address[1]}] CAP: {parts[1]} {parts[2]}")

    

    # Handle NICK command
    def handle_nick(self, client, parts):
        if len(parts) < 2:
            client.send_message("461 * NICK :Not enough parameters")
            print(f"[{client.address[0]}:{client.address[1]}] → Error 461: Not enough parameters")
        else:
            new_nick = parts[1].strip()
            if not re.match(r'^[a-zA-Z][a-zA-Z0-9\-_]*$', new_nick):
                client.send_message(f"432 * {new_nick} :Erroneous nickname")
                client.send_message("NOTICE * :Nickname must start with a letter and can contain only letters, numbers, hyphens, and underscores")
                print(f"[{client.address[0]}:{client.address[1]}] → Error 432: Erronous Nickname")
                return

            for c in self.clients.values():
                if c.nickname == new_nick:
                    client.send_message("433 * " + new_nick + " :Nickname is already in use")
                    print(f"[{client.address[0]}:{client.address[1]}] → Error 433: Nickname already in use")
                    return
                
            if client.nickname:
                for channel in client.channels:
                    # Notify other clients in the channel (we need to broadcast so that HexChat updates the nick)
                    channel.broadcast(":IRCserver" + client.nickname + "!" + client.nickname + "@" + client.address[0] + " NICK :" + new_nick)
            client.nickname = new_nick


    # Handle USER command

    def handle_user(self, client, parts):
        if len(parts) < 5:
            client.send_message("461 * USER :Not enough parameters")
            print(f"[{client.address[0]}:{client.address[1]}] → Error 461: No enough param")
        else:
            client.send_message(": 001 " + client.nickname + " :Welcome to the IRC Network")
            print(f"[{client.address[0]}:{client.address[1]}] → 001 :Welcome to the IRC Network")
            # MOTD File is missing means there is no message to display
            client.send_message(": 422 " + client.nickname + " :MOTD File is missing")
            print(f"[{client.address[0]}:{client.address[1]}] → 422 :MOTD file is missing")

    def handle_log(self, status, nick, time, client):
        logMsg = f"[{client.address[0]}:{client.address[1]}] ← User {nick} {status} at {time}\n"
        print(logMsg)
        # Write the log message to a file
        with open("log.txt", "a") as log:
            log.write(logMsg)

    # Handle JOIN command
    def handle_join(self, client, parts):
        if len(parts) < 2:
            client.send_message(": 461 * JOIN :Not enough parameters")
            print(f"[{client.address[0]}:{client.address[1]}] → Error 461 Not enough parameters")

        else:
            channel_name = parts[1]
            if channel_name not in self.channels:
                self.channels[channel_name] = Channel(channel_name)
            channel = self.channels[channel_name]
            client.join_channel(channel)
            # Notify other clients in the channel
            channel.broadcast(":" + client.nickname + "!" + client.nickname + "@" + client.address[0] + " JOIN " + channel_name)

            client.send_message(": 353 " + client.nickname + " = " + channel_name + " :" + " ".join([c.nickname for c in channel.clients]))
            print(f"{client.address[0]}:{client.address[1]}] → : 353 {client.nickname} : {channel_name}")
            time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.handle_log("connected", client.nickname, time, client)

    # Handle PRIVMSG command
    def handle_privmsg(self, client, parts):
        if len(parts) < 3:

            print(f"[{client.address[0]}:{client.address[1]}] → Error 461 Not enough param")
            client.send_message(":IRCserver 461 * PRIVMSG :Not enough parameters")

        target = parts[1]
        message = " ".join(parts[2:])

        if not message: 
            client.send_message(":IRCserver 412 * PRIVMSG :No text to send")
            print(f"[{client.address[0]}:{client.address[1]}] → Error 412 No text to send")
            return
        
        if target.startswith("#"):
            # Message to a channel
            if target in self.channels:
                self.channels[target].broadcast(":" + client.nickname + "!" + client.nickname + "@" + client.address[0] + " PRIVMSG " + target + " :" + message)
            else:
                client.send_message(":IRCserver 403 * " + target + " :No such channel")
                print(f"[{client.address[0]}:{client.address[1]}] → Error 403 No such channel")
        
        else:
            # Private message to a user
            target_client = None
            for c in self.clients.values():
                if c.nickname == target:
                    target_client = c
                    break
            if target_client:
                target_client.send_message(":" + client.nickname + "!" + client.nickname + "@" + client.address[0] + " PRIVMSG " + target + " :" + message)
                print(f"[{client.address[0]}:{client.address[1]}] → : {client.nickname} sending {message} to {target}")
            else:
                client.send_message(":IRCserver 401 * " + target + " :No such nickname")
                print(f"[{client.address[0]}:{client.address[1]}] → Error 401 No such nickname")

    # Handle QUIT command
    def handle_quit(self, client, parts):
        quit_message = "Client quit"
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.handle_log("disconnected", client.nickname,time, client.address)
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
            print(f"[{client.address[0]}:{client.address[1]}] Error 461 Not enough param")

        else:
            client.send_message(": PONG :" + parts[1])
            print(f"[{client.address[0]}:{client.address[1]}] recieved PING replying with PONG {parts[1]}")


def main():
    SERVER = "::1"
    PORT = 6667
    server = Server(SERVER, PORT)
    server.start()

if __name__ == "__main__":
    main()

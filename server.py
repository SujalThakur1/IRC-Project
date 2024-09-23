import socket
import select

class Channel:
    def __init__(self, name):
        self.name = name
        self.clients = set()

    def add_client(self, client):
        self.clients.add(client)

    def remove_client(self, client):
        self.clients.remove(client)

    def broadcast(self, message, sender=None):
        for client in self.clients:
            if client != sender:
                client.send_message(message)

class Client:
    def __init__(self, socket, address):
        self.socket = socket
        self.address = address
        self.nickname = None
        self.channels = set()
        self.buffer = ""

    def send_message(self, message):
        self.socket.send((message + "\r\n").encode('utf-8'))

    def join_channel(self, channel):
        self.channels.add(channel)
        channel.add_client(self)

    def leave_channel(self, channel):
        self.channels.remove(channel)
        channel.remove_client(self)

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.clients = {}
        self.channels = {}

    def start(self):
        self.socket.bind((self.host, self.port, 0, 0))
        self.socket.listen(5)
        print("IRC Server running on port", self.port)
        
        while True:
            try:
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

    def handle_client(self, client):
        try:
            data = client.socket.recv(2048).decode("utf-8", errors="ignore")
            if not data:
                self.remove_client(client)
            else:
                client.buffer += data
                while "\r\n" in client.buffer:
                    line, client.buffer = client.buffer.split("\r\n", 1)
                    self.handle_command(client, line.strip())
        except Exception as e:
            print("Error handling client", client.address, ":", e)
            self.remove_client(client)

    def remove_client(self, client):
        for channel in list(client.channels):
            client.leave_channel(channel)
        del self.clients[client.socket]
        client.socket.close()
        print("Client", client.address, "disconnected")
    
    def handle_command(self, client, data):
        print(data)
        parts = data.split()
        if not parts:
            return
        command = parts[0].upper()

        if command == "NICK":
            self.handle_nick(client, parts)
        elif command == "USER":
            self.handle_user(client, parts)
        elif command == "JOIN":
            self.handle_join(client, parts)
        elif command == "PRIVMSG":
            self.handle_privmsg(client, parts)
        elif command == "QUIT":
            self.handle_quit(client, parts)
        elif command == "PING":
            self.handle_ping(client, parts)
        else:
            print("Client", client.nickname, "typed:", data)

    def handle_nick(self, client, parts):
        if len(parts) < 2:
            client.send_message("461 * NICK :Not enough parameters")
        else:
            new_nick = parts[1]
            for c in self.clients.values():
                if c.nickname == new_nick:
                    client.send_message("433 * " + new_nick + " :Nickname is already in use")
                    return
            client.nickname = new_nick

    def handle_user(self, client, parts):
        if len(parts) < 5:
            client.send_message("461 * USER :Not enough parameters")
        else:
            client.send_message(": 001 " + client.nickname + " :Welcome to the IRC Network")
            client.send_message(": 422 " + client.nickname + " :MOTD File is missing")

    def handle_join(self, client, parts):
        if len(parts) < 2:
            client.send_message(": 461 * JOIN :Not enough parameters")
        else:
            channel_name = parts[1]
            if channel_name not in self.channels:
                self.channels[channel_name] = Channel(channel_name)
            channel = self.channels[channel_name]
            client.join_channel(channel)
            channel.broadcast(":" + client.nickname + "!" + client.nickname + "@" + client.address[0] + " JOIN " + channel_name)
            client.send_message(": 353 " + client.nickname + " = " + channel_name + " :" + " ".join([c.nickname for c in channel.clients]))

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

    def handle_quit(self, client, parts):
        quit_message = "Client quit"
        if len(parts) > 1:
            quit_message = " ".join(parts[1:])[1:]
        for channel in list(client.channels):
            channel.broadcast(": " + client.nickname + "!" + client.nickname + "@" + client.address[0] + " QUIT :" + quit_message)
            client.leave_channel(channel)
        self.remove_client(client)

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

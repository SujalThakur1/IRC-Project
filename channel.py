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
                try:
                    client.send_message(message)
                # ConnectionError is for connection-related issues
                # BrokenPipeError is for trying to write on a socket which has been shutdown for writing
                except(ConnectionError, BrokenPipeError):
                    print(f"Error: {client.nickname} has disconnected")

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
        try: 
            self.socket.send((message + "\r\n").encode('utf-8'))
        # ConnectionError is for connection-related issues
        # BrokenPipeError is for trying to write on a socket which has been shutdown for writing
        except(ConnectionError, BrokenPipeError):
            print(f"Error: {self.nickname} has disconnected")


    def join_channel(self, channel):
        self.channels.add(channel)
        channel.add_client(self)

    def leave_channel(self, channel):
        self.channels.remove(channel)
        channel.remove_client(self)
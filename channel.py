import datetime

class Channel:
    

    def __init__(self, name):
        self.name = name
        self.clients = set()

    def add_client(self, client):
        self.clients.add(client)

    def remove_client(self, client):
        self.clients.remove(client)

    # Broadcast a message to all clients in the channel except the sender
    def broadcast(self, message, sender=None):
        for client in self.clients:
            if client != sender:
                client.send_message(message)


    #Set is not subscriptable, rmbr to add call to this function
    def display_clients(self):
        self.broadcast(f"There is {len(self.clients)} user(s) in the channel")
        for client in self.clients:
            self.broadcast(f"User: {client.nickname} is in the channel")
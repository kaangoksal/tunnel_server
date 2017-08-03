from queue import Queue
import time


class socket_client(object):

    def __init__(self, username, password, socket_connection):
        self.username = username
        self.password = password
        self.socket_connection = socket_connection
        self.inbox_queue = Queue()
        self.outbox_queue = Queue()
        # Last time that a ping was received in seconds
        self.last_ping = int(round(time.time()))
        self.status = True

    def __str__(self):
        return "Client with object of username: " + self.username



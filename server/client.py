from queue import Queue
import time
import datetime


class socket_client(object):

    def __init__(self, username, password, socket_connection):
        self.username = username
        self.password = password
        self.socket_connection = socket_connection
        self.inbox_queue = Queue()
        self.outbox_queue = Queue()
        # Last time that a ping was received in seconds
        self.last_ping = int(round(time.time()))
        self.ping_timer = None
        self.status = True
        self.connection_time = datetime.datetime.now()

    def __str__(self):
        seconds = int(round(time.time()))
        return "Client with object of username: " + self.username + " last ping " + str(seconds-self.last_ping)



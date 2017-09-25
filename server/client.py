from queue import Queue
import time
import datetime


class socket_client(object):

    def __init__(self, username, password, socket_connection):
        self.username = username
        self.password = password
        # the socket connection of the client
        self.socket_connection = socket_connection
        # Last time that a ping was received in seconds
        self.last_ping = int(round(time.time()))
        self.status = True
        self.connection_time = datetime.datetime.now()


        # These are also seem to be not being used
        self.inbox_queue = Queue()
        self.outbox_queue = Queue()
        # Stores the ping timer object for the client, seems to be unused
        self.ping_timer = None




    def __str__(self):
        seconds = int(round(time.time()))
        return "Client with object of username: " + self.username + " last ping " + str(seconds-self.last_ping)



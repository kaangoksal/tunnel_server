"""
Inspired from
https://github.com/buckyroberts/Turtle/blob/master/Multiple_Clients/server.py

Author: Kaan Goksal
8 JULY 2017


"""

# TODO add SSL
# TODO Implement Logger
# TODO authentication for accept connections, Can use RSA

import socket
import sys
import time
import signal
import threading

from threading import Timer

from queue import Queue
import json
import struct
from Message import Message
from color_print import ColorPrint



"""

Struct is used to add packet length headers to the tcp packets that we are sending.
It helps us to identify packets seperately by reading a single packet without grabbing data from other packet
for example:

If you send two consecutive packets,
packet1 : Ahmed
packet2 : { time: "none", love: "none" }

if you send them fast enough they might end up like this

Ahmed{ time: "none", love: "none"}

therefore your json encode would raise WTF error.

"""


lock = threading.Lock()


client_received = Queue()
outbox = Queue()
UI_queue = Queue()


class TunnelServerCommunicator(object):
    def __init__(self, port, host='', ping_timer=25):
        """
        The init method of the class
        :param port: the server is going to bind
        :param host: the host that the server is going to bind.
        """
        # TODO get these values from config
        self.host = host
        self.port = port
        self.socket = None
        self.all_connections = []
        self.all_clients = {}
        self.ping_timer_time = ping_timer

    def register_signal_handler(self):
        """
        This method registers signal handlers which will do certain stuff before the server terminates
        :return:
        """
        signal.signal(signal.SIGINT, self.quit_gracefully)
        signal.signal(signal.SIGTERM, self.quit_gracefully)
        return

    def quit_gracefully(self, signal=None, frame=None):
        """
            This method shuts down all the connections before turning off.
        """
        print('\nQuitting gracefully')
        for conn in self.all_connections:
            try:
                conn.shutdown(2)
                conn.close()
            except Exception as e:
                print('Could not close connection %s' % str(e))
                # continue
        self.socket.close()
        sys.exit(0)

    def socket_create(self):
        """
        Creates a socket
        :return:
        """
        try:
            self.socket = socket.socket()
        except socket.error as msg:
            print("Socket creation error: " + str(msg))
            # TODO: Added exit
            sys.exit(1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return

    def socket_bind(self):
        """ Bind socket to port and wait for connection from client """
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
        except socket.error as e:
            print("Socket binding error: " + str(e))
            time.sleep(5)
            self.socket_bind()
        return

    def is_client_alive(self, client):
        """
        Checks whether a client is still active on the otherside
        :param client: the username of the client
        :return: true if the client is alive, false if the client is not alive
        """
        client_conn = self.all_clients[client]
        try:

            ping_message = Message("server", client, "utility", "ping")
            client_conn.send(str.encode(ping_message.pack_to_json_string()))

        except Exception as e:
            print("Client communication error " + str(e))
            return False
        return True

    def list_available_clients(self):
        """
        Lists all available clients
        :return: list of connected clients
        """
        connected_clients = self.all_clients.keys()
        return connected_clients

    def get_username_from_connection(self, conn):
        """
        This method returns username from given connection
        :param conn: connection that belongs to some username
        :return: username that the connection belongs to
        """
        dict_copy = self.all_clients
        for username in dict_copy.keys():
            if dict_copy[username] == conn:
                return username


    def read_message_from_connection(self, conn):
        """ Read message length and unpack it into an integer
        :param conn: the connection to the client, it is a socket object
        """
        raw_msglen = self._recvall(conn, 4)
        if not raw_msglen:
            return None

        # We are unpacking a big endian struct which includes
        # the length of the packet, struct makes sure that the header
        # which includes the length is always 4 bytes in length. '>I'
        # indicates that the struct is a unsigned integer big endian
        # CS2110 game strong

        msglen = struct.unpack('>I', raw_msglen)[0]
        # Read the message data
        return self._recvall(conn, msglen)

    @staticmethod
    def _recvall(conn, n):
        """ Helper function to recv n bytes or return None if EOF is hit
        :param n: length of the packet
        :param conn: socket to read from
        """
        data = b''
        while len(data) < n:
            packet = conn.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

    def send_message_to_client(self, client, output_str):
        # TODO throw client not found exception
        # TODO throw socket closed exception
        """ Sends message to the client
         :param client: the username of the client
         :param output_str: string message that will go to the server
        """
        client_socket = self.all_clients[client]

        byte_array_message = str.encode(output_str)
        # We are packing the length of the packet to
        #  unsigned big endian struct to make sure that it is always constant length
        client_socket.send(struct.pack('>I', len(byte_array_message)) + byte_array_message)

    def remove_client(self, client):
        """ closes down the client connection and removes it from the client list
            :param client: the client username that we are removing
        """
        client_conn = self.all_clients[client]

        self.all_clients.pop(client)
        self.all_connections.remove(client_conn)

        # client_conn.shutdown(2)
        client_conn.close()

    def ping(self, username):
        """
        This method constantly pings the users to check whether their connections
        are still alive. It triggers timers
        :param username: the username of the client
        :return: nothing
        """
        message = Message("server", username, "utility", "PING")
        try:
            self.send_message_to_client(username, message.pack_to_json_string())
            # ping timer relaunches itself if the message was successful
            t = Timer(self.ping_timer_time, self.ping, [username])
            t.start()
        except Exception as e:
            print("Exception Occured in PING " + str(e))
            if not self.is_client_alive(username):
                self.remove_client(username)

                client_disconnected_message = Message("server", "server", "event",
                                                      "Client Disconnected " + str(username))
                client_received.put(client_disconnected_message)

    def accept_connections(self):
        """ Accept connections from multiple clients and save to list """
        for c in self.all_connections:
            c.close()
        self.all_connections = []
        # self.all_addresses = []
        while 1:

            try:
                # lock.acquire()
                conn, address = self.socket.accept()
                # If set blocking is 0 server does not wait for message and this try block fails.
                conn.setblocking(1)

                # This is a special message since it is authentication
                json_string = self.read_message_from_connection(conn).decode("utf-8")

                print("Accepting connection " + str(json_string))

                # new_message = Message.json_string_to_message(json_string)
                json_package = json.loads(json_string)
                username = json_package["username"]
                password = json_package["password"]
                hostname = json_package["hostname"]
                host_system_username = json_package["host_system_username"]

                # Ping timer checks whether the client is alive or not by pinging it
                t = Timer(self.ping_timer_time, self.ping, [username])
                t.start()

            except Exception as e:
                ColorPrint.print_message("ERROR", "accept_connections", 'Error accepting connections: %s' % str(e))
                # Loop indefinitely
                continue
                # lock.release()
            # we need setblocking 0 so that select works in server_controller.
            conn.setblocking(0)
            self.all_connections.append(conn)
            # Put the newly connected client to the list
            self.all_clients[username] = conn
            # Push a message to the queue to notify that a new client is connected
            client_connected_message = Message(username, "server", "event", "Connected")

            client_received.put(client_connected_message)

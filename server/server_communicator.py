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
import struct


"""

Struct is used to add packet length headers to the tcp packets that we are sending.
It helps us to identify packets separately by reading a single packet without grabbing data from other packet
for example:

If you send two consecutive packets,
packet1 : Ahmed
packet2 : { time: "none", love: "none" }

if you send them fast enough they might end up like this

Ahmed{ time: "none", love: "none"}

therefore your json encode would raise WTF error.

"""


class SocketCommunicator(object):

    def __init__(self, port, host=''):
        """
        The init method of the class
        :param port: the server is going to bind
        :param host: the host that the server is going to bind.
        """
        self.host = host
        self.port = port
        self.socket = None

        # Dictionary of socket connections
        self.all_connections = []

        # Dictionary of client_username:client object
        self.all_clients = {}

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

    def list_available_client_usernames(self):
        """
        Lists the usernames of the available clients
        :return: list of connected clients usernames as a string list
        """
        connected_clients = self.all_clients.keys()
        return connected_clients

    def get_username_from_connection(self, conn):
        #TODO check whether this works
        """
        This method returns username from given connection
        :param conn: connection that belongs to some username
        :return: username that the connection belongs to
        """
        dict_copy = self.all_clients

        for username in dict_copy.keys():
            if dict_copy[username].socket_connection == conn:
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
        if isinstance(client, str):
            client = self.all_clients[client]

            client_socket = client.socket_connection

            byte_array_message = str.encode(output_str)
            # We are packing the length of the packet to
            #  unsigned big endian struct to make sure that it is always constant length
            client_socket.send(struct.pack('>I', len(byte_array_message)) + byte_array_message)

    # def send_message_to_client_username(self, username, output_str):
    #     # TODO throw client not found exception
    #     # TODO throw socket closed exception
    #     """ Sends message to the client
    #      :param client: the username of the client
    #      :param output_str: string message that will go to the server
    #     """
    #     client = self.all_clients[username]
    #
    #     client_socket = client.socket_connection
    #
    #     byte_array_message = str.encode(output_str)
    #     # We are packing the length of the packet to
    #     #  unsigned big endian struct to make sure that it is always constant length
    #     client_socket.send(struct.pack('>I', len(byte_array_message)) + byte_array_message)

    def get_client_from_username(self, username):

        client = self.all_clients.get(username, None)

        if client is not None:
            return client
        else:
            return None

    def remove_client(self, client):
        """ closes down the client connection and removes it from the client list
            :param client: the client username that we are removing
        """
        client_conn = client.socket_connection
        try:
            self.all_clients.pop(client.username)

            self.all_connections.remove(client_conn)

            # client_conn.shutdown(2)
            client_conn.close()
        except Exception as e:
            # Probably client is already removed
            print("remove_client error " + str(e))


"""
Inspired from
https://github.com/buckyroberts/Turtle/blob/master/Multiple_Clients/server.py

Author: Kaan Goksal
8 JULY 2017


"""

# TODO add SSL
# TODO Revise docs,
# TODO authentication for accept connections, Can use RSA
# TODO Cross device compability?

import socket
import sys
import time
import signal
import struct
import logging
import traceback

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


class ServerSocketLayer(object):

    def __init__(self, port, logger = None, host=''):
        """
        The init method of the class
        :param port: the server is going to bind
        :param host: the host that the server is going to bind.
        """
        self.host = host
        self.port = port
        self.socket = None

        #self.logger = logging.getLogger(__name__)
        self.logger = logger
        print("Socket layer logger", self.logger)
        #self.logger.setLevel(logging.INFO)

        #handler = logging.FileHandler('server.log')

        # this would ruin the server console...
        # console_out = logging.StreamHandler(sys.stdout)
        # self.logger.addHandler(console_out)

        #formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        #handler.setFormatter(formatter)

        #self.logger.addHandler(handler)

        self.logger.info("server started")

    # def register_signal_handler(self):
    #     """
    #     This method registers signal handlers which will do certain stuff before the server terminates
    #     :return:
    #     """
    #     signal.signal(signal.SIGINT, self.quit_gracefully)
    #     signal.signal(signal.SIGTERM, self.quit_gracefully)
    #     return
    def close_connection(self, connection):
        try:
            connection.shutdown(2)
        except Exception as e:
            self.logger.error("[close connection] error while shutting down " + str(e))
        connection.close()

    def socket_create(self):
        """
        Creates a socket
        :return:
        """
        try:
            self.socket = socket.socket()
        except socket.error as e:
            self.logger.error("[socket create] Socket creation error " + str(e))
            self.logger.error("[socket create] " + str(traceback.format_exc()))
            sys.exit(1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return

    def socket_bind(self):
        """ Bind socket to port and wait for connection from client """
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
        except socket.error as e:
            self.logger.error("[socket bind] Socket binding error: " + str(e))
            self.logger.error("[socket bind] " + str(traceback.format_exc()))
            time.sleep(5)
            self.socket_bind()
        return

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

    def send_message_to_socket(self, client_socket, output_str):
        # TODO throw client not found exception
        # TODO throw socket closed exception
        """ Sends message to the client
            :param client: the socket of the client
            :param output_str: string message that will go to the server
        """
        # if isinstance(client, str):
        #     client = self.all_clients[client]
        #
        #     client_socket = client.socket_connection

        byte_array_message = str.encode(output_str)
        # We are packing the length of the packet to
        #  unsigned big endian struct to make sure that it is always constant length
        client_socket.send(struct.pack('>I', len(byte_array_message)) + byte_array_message)

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



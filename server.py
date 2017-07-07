"""
Inspired from
https://github.com/buckyroberts/Turtle/blob/master/Multiple_Clients/server.py

Author: Kaan Goksal


one thread will read and write to the clients
one thread will accept connections
one thread will be user interface



"""

#TODO create a client class
#TODO finish comms
#TODO finish UI
#TODO add SSL
#TODO Implement Logger

import socket
import sys
import time
import signal
import threading
from queue import Queue
import json

"""

This library is used for colorful messages on the command line...
The ideal solution should be making a gui to the command line like in htop or powertop

"""

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

import struct


client_received = Queue()
outbox = Queue()

UI_queue = Queue()


class Tunnel_Server(object):

    def __init__(self, port, host=''):
        #TODO get theese values from config
        self.host = host
        self.port = port
        self.socket = None
        self.all_connections = []
        #self.all_addresses = []
        self.all_clients = {}

    def register_signal_handler(self):
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

    def client_alive(self, client):
        client_conn = self.all_clients[client]
        try:
            client_conn.send(str.encode("ping"))
        except Exception as e:
            print("Socket probably dead eh? " + str(e))
            return False
        return True

    def list_available_clients(self):
        connected_clients = self.all_clients.keys()
        return connected_clients


    def read_message_from_connection(self, conn):
        """ Read message length and unpack it into an integer
        :param conn: the connection to the client, it is a socket object
        """
        raw_msglen = self._recvall(conn, 4)
        if not raw_msglen:
            return None
        # We are unpacking a big endian struct which includes the length of the packet, struct makes sure that the header
        # which includes the length is always 4 bytes in length. '>I' indicates that the struct is a unsigned integer big endian
        # CS2110 game strong
        print("Received message, will process it " + str(raw_msglen))

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
                print("None detected")
                return None
            data += packet
        #print("Debug recvall " + str(data))
        return data

    def send_message_to_client(self, client, output_str):
        #TODO throw client not found exception
        #TODO throw socket closed exception
        """ Sends message to the client
         :param client: the username of the client
         :param output_str: string message that will go to the server
        """
        client_socket = self.all_clients[client]

        byte_array_message = str.encode(output_str)
        #We are packing the lenght of the packet to unsigned big endian struct to make sure that it is always constant length
        client_socket.send(struct.pack('>I', len(byte_array_message)) + byte_array_message)

    def remove_client(self, client):
        """ closes down the client connection and removes it from the client list
            :param client: the client username that we are removing
        """
        client_conn = self.all_clients[client]

        self.all_clients.pop(client)
        self.all_connections.remove(client_conn)


        #client_conn.shutdown(2)
        client_conn.close()

    def accept_connections(self):
        #TODO authentication, Can use RSA

        """ Accept connections from multiple clients and save to list """
        for c in self.all_connections:
            c.close()
        self.all_connections = []
        # self.all_addresses = []
        while 1:
            try:
                conn, address = self.socket.accept()
                conn.setblocking(1)
                #TODO check whether it blocks if server does not send anything after connection

                json_package = self.read_message_from_connection(conn).decode("utf-8")
                json_package = json.loads(json_package)
                address = address + (json_package["hostname"],)
                username = json_package["username"]
                password = json_package["password"]
                #TODO add authentication if problem just kick the client and report
            except Exception as e:
                ColorPrint.print_message("ERROR", "accept_connections", 'Error accepting connections: %s' % str(e))
                # Loop indefinitely
                continue
            self.all_connections.append(conn)
            #self.all_addresses.append(address)
            self.all_clients[username] = conn
            #Put the newly connected client to the list
            #UI_queue.put("A new connection is in the house with " + str(conn) + " " + str (address) ,True)

            client_received.put((username, "event", "connected"))

            #print('\nConnection has been established: {0} ({1})'.format(address[-1], address[0]))
        return


def check_for_messages(server):
    while True:
        for username in list(server.all_clients):
            username_conn = server.all_clients[username]
            # received_message = username_conn.recv(4096)

            received_message = server.read_message_from_connection(username_conn)
            print("first blocking call here")
            if received_message is not None and received_message != b'':
                # print("received " + received_message.decode("utf-8") + " from " + username)
                # print("byte form")
                # print(received_message)
                received_message = received_message.decode("utf-8")
                client_received.put((username, "message", received_message))

            # if not server.client_alive(username):
            #     # print(received_message)
            #     # print("client is dead")
            #     server.remove_client(username)
            #     client_received.put((username, "event", "disconnected"))

        time.sleep(1)
    return

def send_messages(server):
    while True:
        departure_message = outbox.get()

        username, type_of_message, message = departure_message

        server.send_message_to_client(username, message)
        print("Sent Message to client " + str(username) + " " + str(message) + " LEN " + str(len(message)))


def accept_connections(server):
    server.socket_create()
    server.socket_bind()
    server.accept_connections()
    return

def UI(server):

    while True:
        print("Please input command [ssh, read_messages]")
        user_input = input()
        if user_input == "read_messages":
            print("Listing messages")
            print(UI_queue.not_empty)
            while UI_queue.not_empty:
                #UI_queue.get(block=True) #Blocks till a message appears!
                new_block = UI_queue.get()

                username, type_of_event, message = new_block

                if type_of_event is "event":
                    ColorPrint.print_message("OkBLUE", "event from " + str(username), message)
                elif type_of_event is "message":
                    ColorPrint.print_message("NORMAL", "message from " + str(username), message)
        elif user_input == "ssh":
            print("Select Client")
            available_clients = server.list_available_clients()
            i = 0
            for client in available_clients:
                print(str(i) + " " + client)
            user_input = input()

            outbox.put((list(available_clients)[int(user_input)], "action", "SSH"))


        print(user_input)

            #UI_queue.task_done()
    return

def message_routing(server):
    while True:
        if client_received.not_empty:
            new_block = client_received.get()

            username, type_of_event, message = new_block

            if type_of_event is "message":
                UI_queue.put(new_block)
            elif type_of_event is "event":
                UI_queue.put(new_block)




def initialize_threads():
    server = Tunnel_Server(9000)
    server.register_signal_handler()

    accept_connections_thread = threading.Thread(target=accept_connections, args=(server,))
    accept_connections_thread.setName("Comm Accept Thread")
    accept_connections_thread.start()

    receive_thread = threading.Thread(target=check_for_messages, args=(server,))
    receive_thread.setName("Receive Thread")
    receive_thread.start()

    send_thread = threading.Thread(target=send_messages, args=(server,))
    send_thread.setName("Send Thread")
    send_thread.start()

    message_router_thread = threading.Thread(target=message_routing, args=(server,))
    message_router_thread.setName("Message Router Thread")
    message_router_thread.start()

    user_interface_thread = threading.Thread(target=UI, args=(server,))
    user_interface_thread.setName("UI Thread")
    user_interface_thread.start()
    return



initialize_threads()

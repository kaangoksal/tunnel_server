"""
Inspired from
https://github.com/buckyroberts/Turtle/blob/master/Multiple_Clients/server.py

Author: Kaan Goksal
8 JULY 2017

one thread will read and write to the clients
one thread will accept connections
one thread will be user interface

"""

# TODO add SSL
# TODO Implement Logger

import socket
import sys
import time
import signal
import threading
from queue import Queue
import json
import struct
from Message import Message

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


lock = threading.Lock()
client_received = Queue()
outbox = Queue()

UI_queue = Queue()


class TunnelServer(object):
    def __init__(self, port, host=''):
        # TODO get these values from config
        self.host = host
        self.port = port
        self.socket = None
        self.all_connections = []
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

    def is_client_alive(self, client):
        client_conn = self.all_clients[client]
        try:

            ping_message = Message("server", client, "utility", "ping")
            client_conn.send(str.encode(ping_message.pack_to_json_string()))

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

    def accept_connections(self):
        # TODO authentication, Can use RSA

        """ Accept connections from multiple clients and save to list """
        for c in self.all_connections:
            c.close()
        self.all_connections = []
        # self.all_addresses = []
        while 1:

            try:
                # lock.acquire()
                conn, address = self.socket.accept()
                conn.setblocking(1)
                # TODO check whether it blocks if server does not send anything after connection

                # This is a special message since it is authentication
                json_string = self.read_message_from_connection(conn).decode("utf-8")

                print("Accepting connection " + str(json_string))

                # new_message = Message.json_string_to_message(json_string)
                json_package = json.loads(json_string)
                username = json_package["username"]
                password = json_package["password"]
                hostname = json_package["hostname"]
                host_system_username = json_package["host_system_username"]

                # TODO add authentication if problem just kick the client and report
            except Exception as e:
                ColorPrint.print_message("ERROR", "accept_connections", 'Error accepting connections: %s' % str(e))
                # Loop indefinitely
                continue
                # lock.release()
            print("Jumped to here")
            self.all_connections.append(conn)
            # self.all_addresses.append(address)
            self.all_clients[username] = conn

            print("All clients " + str(self.all_clients))
            # Put the newly connected client to the list

            client_connected_message = Message(username, "server", "event", "Connected")

            client_received.put(client_connected_message)


def check_for_messages(server):
    # Implement select plz
    while True:
        for username in list(server.all_clients):
            # TODO there is a blocking call here, implement select()
            username_conn = server.all_clients[username]

            received_message = server.read_message_from_connection(username_conn)

            if received_message is not None and received_message != b'':

                json_string = received_message.decode("utf-8")

                try:
                    new_message = Message.json_string_to_message(json_string)
                    client_received.put(new_message)

                except Exception as e:
                    print("Received unexpected message " + str(e) + " " + received_message)

            elif not server.is_client_alive(username):
                server.remove_client(username)
                client_received.put((username, "event", "disconnected"))

        time.sleep(1)


def send_messages(server):
    while True:
        departure_message = outbox.get()

        # username, type_of_message, message = departure_message

        server.send_message_to_client(departure_message.to, departure_message.pack_to_json_string())

        print("Sent Message to client " + departure_message.pack_to_json_string())


def accept_connections(server):
    server.socket_create()
    server.socket_bind()
    server.accept_connections()
    return


def ui(server):
    while True:
        print("Please input command [ssh, read_messages]")
        user_input = input()
        if user_input == "read_messages":
            print("Listing messages")
            print(UI_queue.not_empty)
            while UI_queue.not_empty:
                # UI_queue.get(block=True) #Blocks till a message appears!
                new_block = UI_queue.get()

                # username, type_of_event, message = new_block

                if new_block.type is "event":
                    ColorPrint.print_message("OkBLUE", "event from " + str(new_block.sender), new_block.payload)
                elif new_block.type is "message":
                    ColorPrint.print_message("NORMAL", "message from " + str(new_block.sender), new_block.payload)

        elif user_input == "ssh":

            print("[SSH MENU] Select Option (put in the number) ")
            print("1)Start SSH")
            print("2)Close SSH Connection")
            print("3)Main Menu")
            user_input = input()
            if user_input == "1":
                print("[SSH MENU 2] Select Client")
                available_clients = server.list_available_clients()
                i = 0
                for client in available_clients:
                    print(str(i) + " " + client)
                print(str(len(available_clients)) + " Cancel")
                user_input = input()

                if int(user_input) < len(available_clients):
                    new_message = Message("server", list(available_clients)[int(user_input)], "action", "SSH-Start")

                    # return_dict = {'type':"action" , "payload": "SSH-Start"}
                    # return_string = json.dumps(return_dict, sort_keys=True, indent=4, separators=(',', ': '))

                    # outbox.put((lists(available_clients)[int(user_input)], "action", return_string))
                    outbox.put(new_message)
                else:
                    pass

            elif user_input == "2":
                print("Select Client")
                available_clients = server.list_available_clients()
                i = 0
                for client in available_clients:
                    print(str(i) + " " + client)
                user_input = input()

                # return_dict = {'type': "action", "payload": "SSH-Stop"}
                # return_string = json.dumps(return_dict, sort_keys=True, indent=4, separators=(',', ': '))
                #
                # outbox.put((list(available_clients)[int(user_input)], "action", return_string))

                close_ssh_message = Message("server", list(available_clients)[int(user_input)], "action", "SSH-Stop")

                outbox.put(close_ssh_message)

            elif user_input == "3":
                continue


def message_routing():
    while True:
        if client_received.not_empty:
            new_block = client_received.get()

            # username, type_of_event, message = new_block

            print("DEBUG message routing " + str(new_block))

            if new_block.type is "message":
                UI_queue.put(new_block)
            elif new_block.type is "event":
                UI_queue.put(new_block)
            elif new_block.type is "result":
                print(new_block.payload)


def initialize_threads():
    server = TunnelServer(9000)
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

    message_router_thread = threading.Thread(target=message_routing)
    message_router_thread.setName("Message Router Thread")
    message_router_thread.start()

    user_interface_thread = threading.Thread(target=ui, args=(server,))
    user_interface_thread.setName("UI Thread")
    user_interface_thread.start()
    return


initialize_threads()

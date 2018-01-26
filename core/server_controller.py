import datetime
import json
import select
import signal
import sys
import threading
import time
import traceback
from queue import Queue

from models.Message import Message
from models.Message import MessageType
from models.client import socket_client
from utility.color_print import ColorPrint


class SocketServerController(object):
    def __init__(self, socket_layer, message_handler, database, logger=None):

        self.logger = logger

        self.database = database

        print("Server controller logger ", self.logger)

        # Dictionary of client_username:client object
        self.all_clients = {}

        # Dictionary of socket connections
        self.all_connections = []
        self.logger.info("Server started")

        self.socket_layer = socket_layer
        self.inbox_queue = Queue()
        self.outbox_queue = Queue()

        self.UI_queue = Queue()

        self.socket_time_out = 1
        self.ping_timer_time = 20
        self.ping_deadline = 60

        self.message_handler = message_handler

        # registers the server to the message handler
        self.message_handler.initialize(self)

        self.status = True

    def start(self):
        """
        Initializes the threads which checks for messages, sends messages, monitors threads, routes messages and also registers
        signal handlers for termination.
        :return:
        """
        self.initialize_threads()
        self.register_signal_handler()

    def send_message_to_client(self, message):
        """
        This is a higher level method for sending messages to the clients, it pushes the message to the queue
        and the thread which is responsible for sending the messages process the message and send it to the socket.
        :param message: message object
        :return: nothing
        """
        self.outbox_queue.put(message)

    def register_signal_handler(self):
        """
        This method registers signal handlers which will do certain stuff before the core terminates
        :return:
        """
        signal.signal(signal.SIGINT, self.quit_gracefully)
        signal.signal(signal.SIGTERM, self.quit_gracefully)
        return

    def quit_gracefully(self):
        """
        This is for termination of the core, it is supposed to cleanup nicely, however due to the code which checks
        for thread health, this does not cleanup nicely.
        :return:
        """
        self.status = False
        print("Shutting down")
        self.logger.info("[quit gracefully] quitting gracefully")
        for conn in self.all_connections:
            try:
                self.socket_layer.close_connection(conn)
            except Exception as e:
                self.logger.error("[quit gracefully] could not close connection " + str(e))
                self.logger.error("[quit gracefully] " + str(traceback.format_exc()))
                # continue
        self.socket_layer.close_connection(self.socket_layer.socket)
        sys.exit(0)

    def ping(self):
        """
        This method constantly pings the users to check whether their connections
        are still alive. It triggers timers
        :return: nothing
        """
        while self.status:
            client_username_list = self.all_clients.keys()
            for client_username in list(client_username_list):
                client_object = self.all_clients.get(client_username, None)
                if client_object is not None:
                    seconds = int(round(time.time()))
                    if seconds - client_object.last_ping < self.ping_deadline:
                        # used to send a ping message
                        pass
                    else:
                        # This means that client was not removed so we can remove it!
                        self.remove_client(client_object)

            time.sleep(self.ping_timer_time)

        print("Ping shutting down")

    def remove_client(self, client, reason=None):
        """
        This method removes the client from the core in a higher level, it creates the appropriate messages,
        logs the time stamp and such. In future mysql will also log sesion time here.
        :param client: the client object that is being removed from the core
        :param reason: will be implemented in future
        :return: nothing, literally nothing
        """
        total_session_time = datetime.datetime.now() - client.connection_time

        ColorPrint.print_message("Warning", "remove_client",
                                 "kicking the client " + str(client.username) + " Reason " + str(reason))

        self.logger.warning("Kicking client  "
                            + str(client.username) + " Total Session Time " + str(
            total_session_time) + " Reason " + str(reason))
        # cleaning up the sockets and such
        client_conn = client.socket_connection
        #TODO remove client from sql table
        try:
            self.all_clients.pop(client.username)

            self.all_connections.remove(client_conn)

            self.socket_layer.close_connection(client_conn)

        except Exception as e:
            # Probably client is already removed
            self.logger.error("[remove client] remove_client error " + str(e))
            self.logger.error("[remove client] " + str(traceback.format_exc()))

        client_disconnected_message = Message("core", "core", "event",
                                              "Client Disconnected " + str(client) + " Reason " + str(reason))
        self.inbox_queue.put(client_disconnected_message)

    def is_client_alive(self, client):
        """
        Checks whether a client is still active on the otherside
        :param client: the username of the client
        :return: true if the client is alive, false if the client is not alive
        """
        seconds = int(round(time.time()))
        if client is None or seconds - client.last_ping < self.ping_deadline:
            return False
        else:
            return True

    def accept_connections(self):
        """
        This method accepts connections, however this method is called by check for messages, if the own core socket
        is readable then this method is called to accept the incoming connection, later on new socket is created!
        This method accepts the connection without authenticating it.
        :return: nothing
        """
        conn, address = self.socket_layer.socket.accept()
        # If set blocking is 0 core does not wait for message and this try block fails.
        conn.setblocking(1)

        # This is a special message since it is authentication
        json_string = self.socket_layer.read_message_from_connection(conn).decode("utf-8")

        print("Accepting connection " + str(json_string))

        self.logger.info("Accepting connection " + str(json_string))

        # new_message = Message.json_string_to_message(json_string)
        json_package = json.loads(json_string)
        username = json_package["username"]
        password = json_package["password"]
        # TODO Check client credidentals

        # hostname = json_package["hostname"]
        # host_system_username = json_package["host_system_username"]

        if self.all_clients.get(username, None) is not None:
            self.logger.info("User reconnected in short time " + str(username))
            # This means that the client reconnected before we noticed it
            old_client = self.all_clients[username]
            self.remove_client(old_client)

        new_client = socket_client(username, password, conn)

        # we need set blocking 0 so that select works in server_controller. With this sockets will not block....
        conn.setblocking(1)
        self.all_connections.append(conn)
        # Put the newly connected client to the list
        self.all_clients[username] = new_client
        # Push a message to the queue to notify that a new client is connected
        client_connected_message = Message(username, "core", "event", "Connected")

        self.inbox_queue.put(client_connected_message)

    def send_messages(self):
        """
        This method sends messages that are in the outbox queue.
        :return:
        """
        while self.status:
            # blocking call
            departure_message = self.outbox_queue.get()
            try:
                self._pass_message_to_comm_layer(departure_message.to, departure_message.pack_to_json_string())
                self.logger.info("Sent message to client " + str(departure_message.pack_to_json_string()))
                # print("Sent Message to client " + departure_message.pack_to_json_string())
            except Exception as e:
                print("Exception occurred in send message " + str(e))
                self.logger.error("Exception occured while sending message " + str(e))
                username = departure_message.to

                client = self.get_client_from_username(username)

                if client is not None and not self.is_client_alive(client):
                    self.remove_client(client)

        print("Send Messages shutting down")

    def check_for_messages(self):
        """
        This method checks for messages using select, if the readable port is the own core port, it means that we have
        an incomming connection request, so we call accept connection for that.
        :return:
        """
        while self.status:
            # print("will do select! ")
            readable, writable, exceptional = select.select(self.all_connections, [], [])

            for connection in readable:
                # print("reading conn " + str(connection))
                if connection is self.socket_layer.socket:
                    try:
                        self.accept_connections()
                    except Exception as e:
                        ColorPrint.print_message("ERROR", "accept_connection, check_for_messages",
                                                 'Error accepting connections: %s' % str(e))
                        self.logger.error("[check_for_messages] Error accepting connection " + str(e))
                        self.logger.error("[check_for_messages] " + str(traceback.format_exc()))
                        # continue the loop
                        continue
                else:

                    try:
                        received_message = self.socket_layer.read_message_from_connection(connection)
                        # print("Received " + str(received_message))

                        username = self.get_username_from_connection(connection)
                        client = self.get_client_from_username(username)

                        if received_message is not None and received_message != b'':
                            json_string = received_message.decode("utf-8")
                            self.logger.info("Received message " + str(json_string) + " from " + str(username))
                            try:
                                new_message = Message.json_string_to_message(json_string)
                                self.inbox_queue.put(new_message)

                                # current_seconds = int(round(time.time()))
                                # client.last_ping = current_seconds

                            except Exception as e:
                                print("Received unexpected message " + str(e) + " " + received_message)
                                self.logger.error("[check_for_messages] received unexpected message "
                                                  + str(received_message) + " " + str(e))
                                self.logger.error("[check_for_messages] " + str(traceback.format_exc()))


                        elif not self.is_client_alive(client):
                            # if the client is spamming us with b'' we should check whether it is dead or not.
                            self.remove_client(client, reason="B-storm")

                    except Exception as e:
                        print("Exception occurred in check_for_messages " + str(e))
                        self.logger.error("[check_for_messages] Exception occured " + str(e))
                        self.logger.error("[check_for_messages] " + str(traceback.format_exc()))
                        username = self.get_username_from_connection(connection)
                        client = self.get_client_from_username(username)

                        if not self.is_client_alive(client) and client is not None:
                            self.remove_client(client)

        print("Read Messages shutting down")

    def message_routing(self):
        """
        This method handles all the queues, it routes the incoming massages to appropriate queue's according to the
        message type
        :return:
        """
        while self.status:

            if self.inbox_queue.not_empty:
                new_block = self.inbox_queue.get()

                # print("DEBUG " + str(new_block))
                self.logger.debug("[message_routing] Routing message " + str(new_block))

                if new_block.type == MessageType.event:
                    self.UI_queue.put(new_block)
                elif new_block.type == MessageType.utility:
                    # self.handle_utility(new_block)
                    self.message_handler.handle_message(new_block)
                elif new_block.type == MessageType.communication:
                    self.handle_comms(new_block)
                else:
                    ColorPrint.print_message("Warning", str(new_block.sender), str(new_block.payload))
                    self.logger.warning(
                        "[Message Router] invalid message type " + str(new_block.sender) + " " + str(new_block.payload))

        print("Message routing shutting down")

    def handle_utility(self, message):
        client = self.get_client_from_username(message.sender)
        seconds = int(round(time.time()))
        client.last_ping = seconds

        ping_payload = {"utility_group": "ping"}
        ping_message = Message("core", message.sender, MessageType.utility, ping_payload)
        self.send_message_to_client(ping_message)

    def handle_comms(self, message):
        self.message_handler.handle_message(message)

    def _pass_message_to_comm_layer(self, client_username, message):
        client = self.all_clients[client_username]
        client_socket = client.socket_connection
        self.socket_layer.send_message_to_socket(client_socket, message)

    def list_available_client_usernames(self):
        """
        Lists the usernames of the available clients
        :return: list of connected clients usernames as a string list
        """
        connected_clients = self.all_clients.keys()
        return connected_clients

    def get_username_from_connection(self, conn):
        # TODO check whether this works
        """
        This method returns username from given connection
        :param conn: connection that belongs to some username
        :return: username that the connection belongs to
        """
        dict_copy = self.all_clients

        for username in dict_copy.keys():
            if dict_copy[username].socket_connection == conn:
                return username

    def get_client_from_username(self, username):

        client = self.all_clients.get(username, None)

        return client

    def initialize_threads(self):
        """
        This method initializes the threads that the core runs on, it also checks whether the threads are dead, if
        they are dead, it revives them, if it can't it reports back.
        :return:
        """
        self.socket_layer.socket_create()
        self.socket_layer.socket_bind()

        """ Accept connections from multiple clients and save to list """
        for c in self.all_connections:
            c.close()
        self.all_connections = [self.socket_layer.socket]

        receive_thread = threading.Thread(target=self.check_for_messages)
        receive_thread.setName("Receive Thread")
        receive_thread.start()

        send_thread = threading.Thread(target=self.send_messages)
        send_thread.setName("Send Thread")
        send_thread.start()

        message_router_thread = threading.Thread(target=self.message_routing)
        message_router_thread.setName("Message Router Thread")
        message_router_thread.start()

        ping_thread = threading.Thread(target=self.ping)
        ping_thread.setName("Ping Thread")
        ping_thread.start()

        # Experimental
        while self.status:
            if not receive_thread.is_alive():
                self.logger.error("[Main Thread] receive thread is dead")
                try:
                    receive_thread = threading.Thread(target=self.check_for_messages)
                    receive_thread.setName("Receive Thread")
                    receive_thread.start()
                except Exception as e:
                    self.logger.error("[Main Thread] Cannot revive receive thread " + str(e))
                    self.logger.error("[Main Thread] " + str(traceback.format_exc()))

            if not send_thread.is_alive():
                self.logger.error("[Main Thread] send thread is dead")
                try:
                    send_thread = threading.Thread(target=self.send_messages)
                    send_thread.setName("Send Thread")
                    send_thread.start()
                except Exception as e:
                    self.logger.error("[Main Thread] Cannot revive send thread " + str(e))
                    self.logger.error("[Main Thread] " + str(traceback.format_exc()))

            if not message_router_thread.is_alive():
                self.logger.error("[Main Thread] message_router thread is dead")
                try:
                    message_router_thread = threading.Thread(target=self.message_routing)
                    message_router_thread.setName("Message Router Thread")
                    message_router_thread.start()
                except Exception as e:
                    self.logger.error("[Main Thread] Cannot revive message router thread " + str(e))
                    self.logger.error("[Main Thread] " + str(traceback.format_exc()))

            if not ping_thread.is_alive():
                self.logger.error("[Main Thread] ping thread is dead")
                try:
                    ping_thread = threading.Thread(target=self.ping)
                    ping_thread.setName("Ping Thread")
                    ping_thread.start()
                except Exception as e:
                    self.logger.error("[Main Thread] Cannot revive ping thread " + str(e))
                    self.logger.error("[Main Thread] " + str(traceback.format_exc()))

            time.sleep(1)
        print("core controller shutting down")

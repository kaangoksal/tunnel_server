
from Message import Message
import logging
from color_print import ColorPrint
import select
import threading
import json
import time

import signal
import sys

from queue import Queue
from server.client import socket_client


class SocketServerController(object):

    def __init__(self, server):

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        handler = logging.FileHandler('server.log')
        handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)
        self.logger.info("Server started")

        self.server = server
        self.inbox_queue = Queue()
        self.outbox_queue = Queue()

        self.UI_queue = Queue()

        self.socket_time_out = 1
        self.ping_timer_time = 20
        self.ping_deadline = 60

        # This object is responsible from reporting events
        self.event_notifier = None
        self.status = True

    def start(self):
        self.initialize_threads()
        self.server.register_signal_handler()

    def register_signal_handler(self):
        """
        This method registers signal handlers which will do certain stuff before the server terminates
        :return:
        """
        signal.signal(signal.SIGINT, self.quit_gracefully)
        signal.signal(signal.SIGTERM, self.quit_gracefully)
        return

    def quit_gracefully(self, signal=None, frame=None):
        self.status = False
        print("Shutting down")
        sys.exit(0)


    def ping(self):
        """
        This method constantly pings the users to check whether their connections
        are still alive. It triggers timers
        :param client: the client object
        :return: nothing
        """
        while self.status:
            client_usernames = self.server.all_clients.keys()
            for client_username in list(client_usernames):
                client = self.server.all_clients.get(client_username, None)
                if client is not None:
                    seconds = int(round(time.time()))
                    if seconds - client.last_ping < self.ping_deadline:
                        payload = {"utility_type": "PING"}
                        message = Message("server", client.username, "utility", json.dumps(payload))
                        self.outbox_queue.put(message)
                    else:
                        # This means that client was not removed so we can remove it!
                        ColorPrint.print_message("Warning", "Ping", "kicking the client " + str(client.username))

                        self.logger.warning("Kicking client, did not reply ping " +str(client.username))

                        self.server.remove_client(client)
                        client_disconnected_message = Message("server", "server", "event",
                                                              "Client Disconnected " + str(client))
                        self.inbox_queue.put(client_disconnected_message)
            time.sleep(self.ping_timer_time)

        print("Ping shutting down")

    def is_client_alive(self, client):
        """
        Checks whether a client is still active on the otherside
        :param client: the username of the client
        :return: true if the client is alive, false if the client is not alive
        """
        #
        # client_conn = self.get_client_from_username(client)

        seconds = int(round(time.time()))
        if client is None or seconds - client.last_ping < self.ping_deadline:
            return False
        else:
            return True

    def accept_connections(self):
        conn, address = self.server.socket.accept()
        # If set blocking is 0 server does not wait for message and this try block fails.
        conn.setblocking(1)

        # This is a special message since it is authentication
        json_string = self.server.read_message_from_connection(conn).decode("utf-8")

        print("Accepting connection " + str(json_string))

        self.logger.info("Acceptiong connection " + str(json_string))

        # new_message = Message.json_string_to_message(json_string)
        json_package = json.loads(json_string)
        username = json_package["username"]
        password = json_package["password"]
        # hostname = json_package["hostname"]
        # host_system_username = json_package["host_system_username"]

        if self.server.all_clients.get(username, None) is not None:
            self.logger.info("User reconnected in short time " + str(username))
            # This means that the client reconnected before we noticed it
            old_client = self.server.all_clients[username]
            self.server.remove_client(old_client)


        new_client = socket_client(username, password, conn)

        # Ping timer checks whether the client is alive or not by pinging it
        # t = Timer(self.ping_timer_time, self.ping, [new_client.username])
        # new_client.ping_timer = t
        # t.start()

        # we need set blocking 0 so that select works in server_controller. With this sockets will not block....
        conn.setblocking(1)
        self.server.all_connections.append(conn)
        # Put the newly connected client to the list
        self.server.all_clients[username] = new_client
        # Push a message to the queue to notify that a new client is connected
        client_connected_message = Message(username, "server", "event", "Connected")

        self.inbox_queue.put(client_connected_message)

    def send_messages(self):
        while self.status:
            # blocking call
            departure_message = self.outbox_queue.get()
            try:
                self.server.send_message_to_client(departure_message.to, departure_message.pack_to_json_string())
                self.logger.info("Sent message to client " + str(departure_message.pack_to_json_string()))
                #print("Sent Message to client " + departure_message.pack_to_json_string())
            except Exception as e:
                print("Exception occurred in send message " + str(e))
                self.logger.error("Exception occured while sending message " + str(e))
                username = departure_message.to

                client = self.server.get_client_from_username(username)

                if client is not None and not self.is_client_alive(client):
                    self.server.remove_client(client)

                    client_disconnected_message = Message("server", "server",
                                                          "event", "Client Disconnected " + str(username))
                    self.logger.warning("[send_messages] removing client " + str(username))

                    self.inbox_queue.put(client_disconnected_message)
        print("Send Messages shutting down")

    def check_for_messages(self):
        while self.status:
            # print("will do select! ")
            readable, writable, exceptional = select.select(self.server.all_connections, [], [])

            # print("Readable " + str(readable))
            # print("All connections " + str(self.server.all_connections))

            for connection in readable:
                #print("reading conn " + str(connection))
                if connection is self.server.socket:
                    try:
                        self.accept_connections()
                    except Exception as e:
                        ColorPrint.print_message("ERROR", "accept_connection, check_for_messages",
                                                 'Error accepting connections: %s' % str(e))
                        self.logger.error("[check_for_messages] Error accepting connection " + str(e))
                        # continue the loop
                        continue
                else:

                    try:
                        received_message = self.server.read_message_from_connection(connection)
                        # print("Received " + str(received_message))

                        username = self.server.get_username_from_connection(connection)
                        client = self.server.get_client_from_username(username)

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
                                self.logger.error("[check_for_messages] received unexpected message " +str(received_message) + " " + str(e))
                        elif not self.is_client_alive(client): # if the client is spamming us with b'' we should check whether it is dead or not.

                            self.server.remove_client(client)

                            client_disconnected_message = Message("server", "server", "event",
                                                                  "Client Disconnected " + str(username))
                            self.logger.warning("[check_for_messages] disconnected client "+ str(username))

                            self.inbox_queue.put(client_disconnected_message)

                    except Exception as e:
                        print("Exception occurred in check_for_messages " + str(e))
                        self.logger.error("[check_for_messages] Exception occured " +str(e))
                        username = self.server.get_username_from_connection(connection)
                        print(username)

                        if not self.is_client_alive(username):

                            self.server.remove_client(username)

                            client_disconnected_message = Message("server", "server", "event",
                                                                  "Client Disconnected " + str(username))
                            self.logger.warning("[check_for_messages] disconnected client " + str(username))

                            self.inbox_queue.put(client_disconnected_message)

        print("Read Messages shutting down")

    def message_routing(self):
        while self.status:

            if self.inbox_queue.not_empty:
                new_block = self.inbox_queue.get()

                #print("DEBUG " + str(new_block))
                self.logger.debug("[message_routing] Routing message " + str(new_block))

                if new_block.type == "message":
                    self.UI_queue.put(new_block)
                elif new_block.type == "event":
                    self.UI_queue.put(new_block)
                elif new_block.type == "result":
                    ColorPrint.print_message("Result", str(new_block.sender), new_block.payload)
                elif new_block.type == "utility":
                    self.handle_utility(new_block)
                else:
                    ColorPrint.print_message("Warning", str(new_block.sender), str(new_block.payload))
        print("Message routing shutting down")

    def handle_utility(self, message):
        client = self.server.get_client_from_username(message.sender)
        seconds = int(round(time.time()))
        client.last_ping = seconds

    def initialize_threads(self):

        # TODO Monitor threads for crashes

        self.server.socket_create()
        self.server.socket_bind()

        """ Accept connections from multiple clients and save to list """
        for c in self.server.all_connections:
            c.close()
        self.server.all_connections = [self.server.socket]

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
                receive_thread = threading.Thread(target=self.check_for_messages)
                receive_thread.setName("Receive Thread")
                receive_thread.start()

            if not send_thread.is_alive():
                self.logger.error("[Main Thread] send thread is dead")
                send_thread = threading.Thread(target=self.send_messages)
                send_thread.setName("Send Thread")
                send_thread.start()

            if not message_router_thread.is_alive():
                self.logger.error("[Main Thread] message_router thread is dead")
                message_router_thread = threading.Thread(target=self.message_routing)
                message_router_thread.setName("Message Router Thread")
                message_router_thread.start()

            if not ping_thread.is_alive():
                self.logger.error("[Main Thread] ping thread is dead")
                ping_thread = threading.Thread(target=self.ping)
                ping_thread.setName("Ping Thread")
                ping_thread.start()

            time.sleep(1)
        print("server controller shutting down")




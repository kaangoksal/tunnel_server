
from Message import Message
from threading import Timer
from color_print import ColorPrint
import select
import threading
import json
import time
from queue import Queue
from server.client import socket_client


class SocketServerController(object):

    def __init__(self, server):
        self.server = server
        self.inbox_queue = Queue()
        self.outbox_queue = Queue()

        self.UI_queue = Queue()

        self.socket_time_out = 1
        self.ping_timer_time = 20
        self.ping_deadline = 25

    def start(self):
        self.initialize_threads()
        self.server.register_signal_handler()

    def ping(self, client):
        """
        This method constantly pings the users to check whether their connections
        are still alive. It triggers timers
        :param client: the client object
        :return: nothing
        """

        seconds = int(round(time.time()))
        if not (seconds - client.last_ping > self.ping_deadline):

            payload = {"utility_type": "PING"}

            message = Message("server",
                                  client.username,
                                  "utility", json.dumps(payload))

            # self.server.send_message_to_client(client.username, message.pack_to_json_string())
            self.outbox_queue.put(message)
            # ping timer relaunches itself if the message was successful
            t = Timer(self.ping_timer_time, self.ping, [client])
            t.start()
        elif not self.server.is_client_alive(client):
            self.server.remove_client(client)
            client_disconnected_message = Message("server", "server", "event", "Client Disconnected " + str(client))
            self.inbox_queue.put(client_disconnected_message)

    def accept_connections(self):
        # TODO incorporate different types of clients!
        self.server.socket_create()
        self.server.socket_bind()

        """ Accept connections from multiple clients and save to list """
        for c in self.server.all_connections:
            c.close()
        self.server.all_connections = []

        while 1:

            try:

                conn, address = self.server.socket.accept()
                # If set blocking is 0 server does not wait for message and this try block fails.
                conn.setblocking(1)

                # This is a special message since it is authentication
                json_string = self.server.read_message_from_connection(conn).decode("utf-8")

                print("Accepting connection " + str(json_string))

                # new_message = Message.json_string_to_message(json_string)
                json_package = json.loads(json_string)
                username = json_package["username"]
                password = json_package["password"]
                # hostname = json_package["hostname"]
                # host_system_username = json_package["host_system_username"]

                if self.server.all_clients.get(username, None) is not None:
                    # This means that the client reconnected before we noticed it
                    self.server.remove_client(self.server.all_clients[username])

                new_client = socket_client(username, password, conn)

                # Ping timer checks whether the client is alive or not by pinging it
                t = Timer(self.ping_timer_time, self.ping, [new_client])
                t.start()

            except Exception as e:
                ColorPrint.print_message("ERROR", "accept_connections", 'Error accepting connections: %s' % str(e))
                # Loop indefinitely
                continue

            # we need set blocking 0 so that select works in server_controller. With this sockets will not block....
            conn.setblocking(1)
            self.server.all_connections.append(conn)
            # Put the newly connected client to the list
            self.server.all_clients[username] = new_client
            # Push a message to the queue to notify that a new client is connected
            client_connected_message = Message(username, "server", "event", "Connected")

            self.inbox_queue.put(client_connected_message)

    def send_messages(self):
        while True:
            # blocking call
            departure_message = self.outbox_queue.get()
            try:
                self.server.send_message_to_client(departure_message.to, departure_message.pack_to_json_string())

                print("Sent Message to client " + departure_message.pack_to_json_string())
            except Exception as e:
                print("Exception occurred in send message " + str(e))
                username = departure_message.to

                client = self.server.get_client_from_username(username)

                if client is not None and not self.server.is_client_alive(username):
                    self.server.remove_client(client)

                    client_disconnected_message = Message("server", "server",
                                                          "event", "Client Disconnected " + str(username))

                    self.inbox_queue.put(client_disconnected_message)

    def check_for_messages(self):
        while True:
            # print("will do select! ")
            readable, writable, exceptional = select.select(self.server.all_connections, [], [])

            print("Readable " + str(readable))
            # print("All connections " + str(self.server.all_connections))

            for connection in readable:
                print("reading conn " + str(connection))
                if connection is self.server.socket:
                    try:
                        print("bout to accept")
                        conn, address = self.server.socket.accept()
                        # If set blocking is 0 server does not wait for message and this try block fails.
                        conn.setblocking(1)

                        # This is a special message since it is authentication
                        print("reading from connectione")
                        json_string = self.server.read_message_from_connection(conn).decode("utf-8")

                        print("Accepting connection " + str(json_string))

                        # new_message = Message.json_string_to_message(json_string)
                        json_package = json.loads(json_string)
                        username = json_package["username"]
                        password = json_package["password"]
                        # hostname = json_package["hostname"]
                        # host_system_username = json_package["host_system_username"]

                        new_client = socket_client(username, password, conn)

                        # Ping timer checks whether the client is alive or not by pinging it
                        t = Timer(self.ping_timer_time, self.ping, [new_client])
                        t.start()

                    except Exception as e:
                        ColorPrint.print_message("ERROR", "accept_connections",
                                                 'Error accepting connections: %s' % str(e))
                        # Loop indefinitely
                        continue

                    # we need set blocking 0 so that select works in server_controller. With this sockets will not block....
                    conn.setblocking(1)
                    self.server.all_connections.append(conn)
                    # Put the newly connected client to the list
                    self.server.all_clients[username] = new_client
                    # Push a message to the queue to notify that a new client is connected
                    client_connected_message = Message(username, "server", "event", "Connected")

                    self.inbox_queue.put(client_connected_message)

                else:
                    try:
                        received_message = self.server.read_message_from_connection(connection)
                        # print("Received " + str(received_message))

                        if received_message is not None and received_message != b'':
                            json_string = received_message.decode("utf-8")

                            try:
                                new_message = Message.json_string_to_message(json_string)
                                self.inbox_queue.put(new_message)

                            except Exception as e:
                                print("Received unexpected message " + str(e) + " " + received_message)
                        elif not self.server.is_client_alive(self.server.get_username_from_connection(connection)):
                            username = self.server.get_username_from_connection(connection)
                            client = self.server.get_client_from_username(username)
                            self.server.remove_client(client)

                            client_disconnected_message = Message("server", "server", "event",
                                                                  "Client Disconnected " + str(username))

                            self.inbox_queue.put(client_disconnected_message)

                    except Exception as e:
                        print("Exception occurred in check_for_messages " + str(e) +
                              " All Clients dict " + str(self.server.all_clients))

                        username = self.server.get_username_from_connection(connection)
                        print(username)

                        if not self.server.is_client_alive(username):

                            self.server.remove_client(username)

                            client_disconnected_message = Message("server", "server", "event",
                                                                  "Client Disconnected " + str(username))

                            self.inbox_queue.put(client_disconnected_message)

    def ui(self):
        while True:
            try:
                print("Please input command [ssh, read_messages, info]")
                user_input = input()
                if user_input == "read_messages":
                    self.ui_read_messages()

                elif user_input == "ssh":
                    self.ui_ssh()
                elif user_input == "info":
                    self.ui_info()

            except EOFError as e:
                ColorPrint.print_message("Error", "UI", "Exception occurred " + str(e))

    def ui_info(self):
        print("[Information Panel]")
        print("-------Connected Clients--------")

        dict_copy = self.server.all_clients

        counter = 0
        for username in dict_copy.keys():
            client = dict_copy[username]
            current_seconds = int(round(time.time()))
            print(str(counter) + ") " + client.username + " Last ping " + str(client.last_ping- current_seconds))
            counter += 1

        print("------All connections-------")
        counter = 0
        for connection in self.server.all_connections:
            if counter > 0:
                print(str(counter) + ") " + str(connection) + "derived username " + self.server.get_username_from_connection(connection))
            else:
                print(str(counter) + ") " + str(connection))
            counter += 1

        # print ("select shit")
        # readable, writable, exceptional = \
        #     select.select(self.server.all_connections,
        #                   self.server.all_connections, self.server.all_connections)
        # print(readable)

    def ui_read_messages(self):
        print("Listing messages")
        print(self.UI_queue.not_empty)

        # TODO fix blocking here

        while not self.UI_queue.empty():
            # UI_queue.get(block=True) #Blocks till a message appears!
            new_block = self.UI_queue.get()

            # username, type_of_event, message = new_block

            if new_block.type is "event":
                ColorPrint.print_message("Event", str(new_block.sender), new_block.payload)
            elif new_block.type is "message":
                ColorPrint.print_message("Message", str(new_block.sender), new_block.payload)

    def ui_ssh(self):
        print("[SSH MENU] Select Option (put in the number) ")
        print("1)Start SSH")
        print("2)Close SSH Connection")
        print("3)Main Menu")

        user_input = input()

        if user_input == "1":
            print("[SSH MENU 2] Select Client")
            available_clients = self.server.list_available_client_usernames()
            i = 0
            for client in available_clients:
                print(str(i) + " " + client)
                i += 1
            print(str(len(available_clients)) + " Cancel")

            # Never trust the user
            try:
                user_input = input()
                if int(user_input) < len(available_clients):

                    parameters = {"local_port": 22,
                                  "remote_port": 7005,
                                  "name": "shell connection"}

                    payload = {"action_type": "SSH",
                               "parameters": json.dumps(parameters),
                               "command": "SSH-Start"}

                    new_message = Message("server",
                                          list(available_clients)[int(user_input)],
                                          "action", json.dumps(payload))

                    self.outbox_queue.put(new_message)
                else:
                    pass
            except Exception as e:
                print("Invalid input " + str(e))

        elif user_input == "2":
            print("[SSH MENU] Select Client to Close Connection")
            available_clients = self.server.list_available_client_usernames()
            i = 0
            for client in available_clients:
                print(str(i) + " " + client)
                i += 1

            print(str(len(available_clients)) + " Cancel")
            try:
                user_input = input()
                if int(user_input) < len(available_clients):

                    parameters = {"name": "shell connection"}

                    payload = {"action_type": "SSH",
                               "parameters": json.dumps(parameters),
                               "command": "SSH-Stop"}

                    close_ssh_message = Message("server",
                                                list(available_clients)[int(user_input)],
                                                "action",
                                                json.dumps(payload))

                    self.outbox_queue.put(close_ssh_message)
                else:
                    pass
            except Exception as e:
                ColorPrint.print_message("Error", "UI", "Invalid input " + str(e))

    def message_routing(self):
        while True:

            if self.inbox_queue.not_empty:
                new_block = self.inbox_queue.get()

                print("DEBUG " + str(new_block))

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

    def handle_utility(self, message):
        client = self.server.get_client_from_username(message.sender)
        seconds = int(round(time.time()))
        client.last_ping = seconds

    def initialize_threads(self):

        # TODO Monitor threads for crashes

        # accept_connections_thread = threading.Thread(target=self.accept_connections)
        # accept_connections_thread.setName("Comm Accept Thread")
        # accept_connections_thread.start()

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

        user_interface_thread = threading.Thread(target=self.ui)
        user_interface_thread.setName("UI Thread")
        user_interface_thread.start()


from Message import Message
from Server.server import UI_queue
from Server.server import client_received
from Server.server import outbox
from Server.server import TunnelServer
from color_print import ColorPrint
import select
import time
import threading
import json


class ServerController(object):

    def __init__(self, server):
        self.server = server
        # self.initialize_threads() #this starts serving..

    def start(self):
        self.initialize_threads()
        self.server.register_signal_handler()

    def check_for_messages(self):
        # Implement select plz
        while True:
            timeout = 1
            readable, writable, exceptional = \
                select.select(self.server.all_connections,
                              self.server.all_connections, self.server.all_connections, timeout)
            # print("Readable " + str(readable))
            # print("All connections " + str(self.server.all_connections))
            for connection in readable:
                try:
                    received_message = self.server.read_message_from_connection(connection)
                    # print("Received " + str(received_message))

                    if received_message is not None and received_message != b'':
                        json_string = received_message.decode("utf-8")

                        try:
                            new_message = Message.json_string_to_message(json_string)
                            client_received.put(new_message)

                        except Exception as e:
                            print("Received unexpected message " + str(e) + " " + received_message)

                    # elif not self.server.is_client_alive(username):
                    #          self.server.remove_client(username)
                    #          client_received.put((username, "event", "disconnected"))
                except Exception as e:
                    print("Exception occurred in check_for_messages " + str(e))

                    username = self.server.get_username_from_connection(connection)

                    if not self.server.is_client_alive(username):
                        self.server.remove_client(username)

                        client_disconnected_message = Message("server", "server", "event", "Client Disconnected " + str(username))

                        client_received.put(client_disconnected_message)

            time.sleep(1)

    def send_messages(self):
        while True:
            departure_message = outbox.get()
            try:
                self.server.send_message_to_client(departure_message.to, departure_message.pack_to_json_string())

                print("Sent Message to client " + departure_message.pack_to_json_string())
            except Exception as e:
                print("Exception occured in send message " + str(e))
                username = departure_message.to

                if not self.server.is_client_alive(username):
                    self.server.remove_client(username)

                    client_disconnected_message = Message("server", "server", "event", "Client Disconnected " + str(username))

                    client_received.put(client_disconnected_message)


    def accept_connections(self):
        self.server.socket_create()
        self.server.socket_bind()
        self.server.accept_connections()
        return

    def ui(self):
        while True:
            try:
                print("Please input command [ssh, read_messages]")
                user_input = input()
                if user_input == "read_messages":
                    print("Listing messages")
                    print(UI_queue.not_empty)

                    # TODO fix blocking here

                    while not UI_queue.empty():
                        # UI_queue.get(block=True) #Blocks till a message appears!
                        new_block = UI_queue.get()

                        # username, type_of_event, message = new_block

                        if new_block.type is "event":
                            ColorPrint.print_message("OkBLUE", "event from " + str(new_block.sender), new_block.payload)
                        elif new_block.type is "message":
                            ColorPrint.print_message("NORMAL", "message from " +
                                                     str(new_block.sender), new_block.payload)

                elif user_input == "ssh":

                    print("[SSH MENU] Select Option (put in the number) ")
                    print("1)Start SSH")
                    print("2)Close SSH Connection")
                    print("3)Main Menu")

                    user_input = input()

                    if user_input == "1":
                        print("[SSH MENU 2] Select Client")
                        available_clients = self.server.list_available_clients()
                        i = 0
                        for client in available_clients:
                            print(str(i) + " " + client)
                            i = i + 1
                        print(str(len(available_clients)) + " Cancel")

                        # Never trust the user
                        try:
                            user_input = input()
                            if int(user_input) < len(available_clients):
                                parameters = {"local_port": 22, "remote_port": 7005, "name": "shell connection"}

                                payload = {"action_type": "SSH", "parameters": json.dumps(parameters, sort_keys=True, indent=4, separators=(',', ': ')), "command": "SSH-Start"}

                                new_message = Message("server",
                                                      list(available_clients)[int(user_input)],
                                                      "action", json.dumps(payload, sort_keys=True, indent=4, separators=(',', ': ')))

                                outbox.put(new_message)
                            else:
                                pass
                        except Exception as e:
                            print("Invalid input " + str(e))

                    elif user_input == "2":
                        print("[SSH MENU] Select Client to Close Connection")
                        available_clients = self.server.list_available_clients()
                        i = 0
                        for client in available_clients:
                            print(str(i) + " " + client)
                            i = i + 1

                        print(str(len(available_clients)) + " Cancel")
                        try:
                            user_input = input()
                            if int(user_input) < len(available_clients):
                                close_ssh_message = Message("server",
                                                            list(available_clients)[int(user_input)],
                                                            "action",
                                                            "SSH-Stop")
                                outbox.put(close_ssh_message)
                            else:
                                pass
                        except Exception as e:
                            print("Invalid input " + str(e))

                    elif user_input == "3":
                        continue
            except EOFError as e:
                print(str(e))

    @staticmethod
    def message_routing():
        while True:

            if client_received.not_empty:
                new_block = client_received.get()

                # username, type_of_event, message = new_block

                print("DEBUG mr " + str(new_block))

                if new_block.type == "message":
                    UI_queue.put(new_block)
                elif new_block.type == "event":
                    UI_queue.put(new_block)
                elif new_block.type == "result":
                    print(new_block.payload)
                else:
                    print("Message not routable " + str(new_block.payload))

    def initialize_threads(self):

        # TODO Monitor threads for crashes

        accept_connections_thread = threading.Thread(target=self.accept_connections)
        accept_connections_thread.setName("Comm Accept Thread")
        accept_connections_thread.start()

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



        return

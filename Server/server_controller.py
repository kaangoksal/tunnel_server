
from Message import Message
from Server.server import UI_queue
from Server.server import client_received
from Server.server import outbox
from Server.server import TunnelServer
from color_print import ColorPrint
import time
import threading


class ServerController(object):

    def __init__(self, server):
        self.server = server
        # self.initialize_threads() #this starts serving..

    def start(self):
        self.initialize_threads()

    def check_for_messages(self):
        # Implement select plz
        while True:
            for username in list(self.server.all_clients):
                # TODO there is a blocking call here, implement select()
                username_conn = self.server.all_clients[username]

                received_message = self.server.read_message_from_connection(username_conn)

                if received_message is not None and received_message != b'':

                    json_string = received_message.decode("utf-8")

                    try:
                        new_message = Message.json_string_to_message(json_string)
                        client_received.put(new_message)

                    except Exception as e:
                        print("Received unexpected message " + str(e) + " " + received_message)

                elif not self.server.is_client_alive(username):
                    self.server.remove_client(username)
                    client_received.put((username, "event", "disconnected"))

            time.sleep(1)

    def send_messages(self):
        while True:
            departure_message = outbox.get()

            self.server.send_message_to_client(departure_message.to, departure_message.pack_to_json_string())

            print("Sent Message to client " + departure_message.pack_to_json_string())

    def accept_connections(self):
        self.server.socket_create()
        self.server.socket_bind()
        self.server.accept_connections()
        return

    def ui(self):
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
                    available_clients = self.server.list_available_clients()
                    i = 0
                    for client in available_clients:
                        print(str(i) + " " + client)
                    print(str(len(available_clients)) + " Cancel")
                    user_input = input()

                    if int(user_input) < len(available_clients):
                        new_message = Message("server", list(available_clients)[int(user_input)], "action", "SSH-Start")

                        outbox.put(new_message)
                    else:
                        pass

                elif user_input == "2":
                    print("[SSH MENU] Select Client to Close Connection")
                    available_clients = self.server.list_available_clients()
                    i = 0
                    for client in available_clients:
                        print(str(i) + " " + client)
                    i = 0
                    for client in available_clients:
                        print(str(i) + " " + client)
                    print(str(len(available_clients)) + " Cancel")

                    user_input = input()
                    if int(user_input) < len(available_clients):
                        close_ssh_message = Message("server", list(available_clients)[int(user_input)], "action", "SSH-Stop")
                        outbox.put(close_ssh_message)
                    else:
                        pass

                elif user_input == "3":
                    continue

            print("cycle!")

    @staticmethod
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

    def initialize_threads(self):
        server = TunnelServer(9000)
        server.register_signal_handler()

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

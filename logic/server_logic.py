from color_print import ColorPrint
import time
from Message import Message
import json
import signal
import sys
import threading
import datetime


class ServerLogic(object):
    def __init__(self):
        self.server_controller = None
        self.user_interface_thread = None

    def start(self):
        self.user_interface_thread = threading.Thread(target=self.ui)
        self.user_interface_thread.setName("UI Thread")
        self.user_interface_thread.start()

    def register_signal_handler(self):
        """
        This method registers signal handlers which will do certain stuff before the server terminates
        :return:
        """
        signal.signal(signal.SIGINT, self.quit_gracefully)
        signal.signal(signal.SIGTERM, self.quit_gracefully)
        return

    def quit_gracefully(self, signal=None, frame=None):
        print("Shutting down")
        sys.exit(0)

    def ui(self):
        while self.server_controller.status:
            try:
                print("Please input command [ssh, read_messages, info, tools]")
                user_input = input()
                if user_input == "read_messages":
                    self.ui_read_messages()

                elif user_input == "ssh":
                    self.ui_ssh()
                elif user_input == "info":
                    self.ui_info()
                elif user_input == "tools":
                    self.ui_tools()

            except EOFError as e:
                ColorPrint.print_message("Error", "UI", "Exception occurred " + str(e))
        print("UI Terminating")

    def ui_tools(self):
        print("[Tools Panel]")
        print("--------------Options------------")
        print("\n")
        print("1) Disconnect a client")
        user_input = input()
        if user_input == "1":

            available_clients = self.server_controller.list_available_client_usernames()
            i = 0
            for client in available_clients:
                print(str(i) + " " + client)
                i += 1
            print(str(len(available_clients)) + " Cancel")

            # Never trust the user
            try:
                user_input = input()
                if int(user_input) < len(available_clients):

                    user = list(available_clients)[int(user_input)]
                    self.server_controller.remove_client(self.server_controller.all_clients[user])

                else:
                    pass
            except Exception as e:
                print("Invalid input " + str(e))



    def ui_info(self):
        print("[Information Panel]")
        print("-------Connected Clients--------")
        print("\n")

        dict_copy = self.server_controller.all_clients

        counter = 0
        for username in dict_copy.keys():
            client = dict_copy[username]
            current_seconds = int(round(time.time()))
            print(str(counter) + ") " + client.username + " Last ping " + str(client.last_ping - current_seconds) + " "
                  + " Connection Time " + str(datetime.datetime.now() - client.connection_time))
            counter += 1
        print("\n")
        print("------All connections-------")
        print("\n")
        counter = 0
        for connection in self.server_controller.all_connections:
            if counter > 0:
                (ip, port) = connection.getpeername()
                print(str(counter) + ") " + str(
                    ip) + " username " + self.server_controller.get_username_from_connection(connection))
            else:
                print(str(counter) + ") " + str(connection))
            counter += 1
        print("\n")
        print("-------Running threads----------")
        print("\n")
        for thread in threading.enumerate():
            print(thread)
        print("\n")

    def ui_read_messages(self):
        print("Listing messages")
        print(self.server_controller.UI_queue.not_empty)

        # TODO fix blocking here

        while not self.server_controller.UI_queue.empty():
            # UI_queue.get(block=True) #Blocks till a message appears!
            new_block = self.server_controller.UI_queue.get()

            # username, type_of_event, message = new_block

            if new_block.type is "event":
                ColorPrint.print_message("Event", str(new_block.sender), new_block.payload + " -Message Created " + str(new_block.date))
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
            available_clients = self.server_controller.list_available_client_usernames()
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

                    self.server_controller.outbox_queue.put(new_message)
                else:
                    pass
            except Exception as e:
                print("Invalid input " + str(e))

        elif user_input == "2":
            print("[SSH MENU] Select Client to Close Connection")
            available_clients = self.server_controller.list_available_client_usernames()
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

                    self.server_controller.outbox_queue.put(close_ssh_message)
                else:
                    pass
            except Exception as e:
                ColorPrint.print_message("Error", "UI", "Invalid input " + str(e))
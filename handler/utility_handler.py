"""
This module is still in development
Author: Kaan Goksal
Copyright: Kaan Goksal
Date: 4 September 2017

"""

from Message import Message
from Message import MessageType
# TODO implement logger


class UtilityHandler(object):
    def __init__(self, server=None):
        self.utility_handlers = {}
        self.server = server

    def handle_message(self, message):
        payload = message.payload
        utility_group = payload["utility_group"]
        if utility_group == "ping":
            self.handle_ping(message)
        else:
            pass

    def handle_ping(self, message):
        client = self.server.get_client_from_username(message.sender)
        client.update_last_ping()

        ping_payload = {"utility_group": "ping"}
        ping_message = Message("server", message.sender, MessageType.utility, ping_payload)
        self.server.send_message_to_client(ping_message)

    def __str__(self):
        return "MessageHandler Object with " + str(self.utility_handlers)


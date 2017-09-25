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
        if message.type == "utility":
            payload = message.payload
            utility_group = payload["utility_group"]
            if utility_group == "ping":
                ping_payload = {"utility_group": "ping"}
                ping_message = Message("server", message.sender, MessageType.utility, ping_payload )
                self.server.send_message_to_client(ping_message)
            else:
                pass

    def __str__(self):
        return "MessageHandler Object with " + str(self.utility_handlers)


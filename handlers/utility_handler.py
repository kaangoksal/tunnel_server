"""
This module is still in development
Author: Kaan Goksal
Copyright: Kaan Goksal
Date: 4 September 2017

"""

from models.Message import Message
from models.Message import MessageType
from handlers.handler import Handler


class UtilityHandler(Handler):
    def __init__(self, server=None):
        Handler.__init__(self)

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
        ping_message = Message("core", message.sender, MessageType.utility, ping_payload)
        self.logger.debug("[handle_ping], replying ping message " + str(ping_message))
        self.server.send_message_to_client(ping_message)

    def __str__(self):
        return "UtilityHandler Object with " + str(self.handlers)


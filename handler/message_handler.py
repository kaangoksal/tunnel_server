"""
This module is still in development
Author: Kaan Goksal
Copyright: Kaan Goksal
Date: 4 September 2017

"""

from Message import Message
# TODO implement logger


class MessageHandler(object):
    def __init__(self, server=None):
        self.handlers = {}
        self.server = server

    def handle_message(self, message):
        if message.type in self.handlers:
            handler = self.handlers[message.type]
            handler.handle_message(message)
        else:
            # This is a malignant action! Report the incident
            print("Error, no handler found for " + str(message))

    def __str__(self):
        return "MessageHandler Object with " + str(self.handlers)


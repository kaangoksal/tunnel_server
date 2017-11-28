"""
This module is still in development
Author: Kaan Goksal
Copyright: Kaan Goksal
Date: 4 September 2017

"""


# TODO implement logger

from handlers.handler import Handler


class MessageHandler(Handler):

    def __init__(self, server=None):
        Handler.__init__(self)

    def handle_message(self, message):

        specific_handler = self.handlers[str(message.type)]

        if specific_handler is not None:
            specific_handler.handle_message(message)
        else:
            # This is a malignant action! Report the incident
            print("Error, no handlers found for " + str(message))

    def __str__(self):
        return "MessageHandler Object with " + str(self.handlers)


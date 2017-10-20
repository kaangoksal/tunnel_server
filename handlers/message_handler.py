"""
This module is still in development
Author: Kaan Goksal
Copyright: Kaan Goksal
Date: 4 September 2017

"""


# TODO implement logger


class MessageHandler(object):
    def __init__(self, server=None):
        self.handlers = {}
        self.server = server
        self.logger = None

    def initialize(self, server):
        self.server = server

        if self.server is not None:
            self.logger = self.server.logger

            for key in list(self.handlers.keys()):
                # initializes the other handlers
                handler = self.handlers[key]
                handler.initialize(self.server)
        else:
            print("Error! Message Handler is not initialized properly")

    def register_handler(self, handler, handler_type):
        """
        This is for registering message handlers! I did not decide whether this can be called after initialize...
        :param handler:
        :param handler_type:
        :return:
        """
        if handler_type is not None or handler is not None:
            self.handlers[handler_type] = handler

    def handle_message(self, message):
        if message.type in self.handlers:
            handler = self.handlers[message.type]
            handler.handle_message(message)
        else:
            # This is a malignant action! Report the incident
            print("Error, no handlers found for " + str(message))

    def __str__(self):
        return "MessageHandler Object with " + str(self.handlers)


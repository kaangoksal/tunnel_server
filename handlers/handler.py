class Handler(object):

    def __init__(self, server=None):
        self.handlers = {}
        self.server = server
        self.logger = None

    def initialize(self, server):
        """
        initializes the handler object, gives reference to the main server object so that the child handlers, and the
        handler itself can interact with the server to send message and so.
        :param server: the server controller object
        :return: nothing
        """
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


# TODO implement logger
# TODO implement config parser

from handler.message_handler import MessageHandler
from handler.utility_handler import UtilityHandler
from server.server_controller import SocketServerController
from server.server_socket_layer import ServerSocketLayer
from logic.server_logic import ServerLogic
from Message import MessageType


if __name__ == "__main__":
    # Socket communicator is for talking with the clients
    server = ServerSocketLayer(9000)
    # Server controller pings receives and sends messages and checks on the clients
    server_controller = SocketServerController(server)


    message_handler = MessageHandler(server_controller)
    utility_handler = UtilityHandler(server_controller)
    message_handler.handlers[MessageType.utility] = utility_handler


    server_controller.message_handler = message_handler

    # server logic is the ui which allows us to create and send commands to the clients and also see info about them!
    ui_logic = ServerLogic()
    ui_logic.server_controller = server_controller
    #we start the server_controller first, and then the ui.
    ui_logic.start()
    server_controller.start()




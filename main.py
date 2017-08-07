
# TODO implement logger
# TODO implement config parser


from server.server_controller import SocketServerController
from server.server_communicator import SocketCommunicator
from logic.server_logic import ServerLogic


if __name__ == "__main__":
    # Socket communicator is for talking with the clients
    server = SocketCommunicator(9000)
    # Server controller pings receives and sends messages and checks on the clients
    server_controller = SocketServerController(server)
    # server logic is the ui which allows us to create and send commands to the clients and also see info about them!
    ui_logic = ServerLogic()
    ui_logic.server_controller = server_controller
    #we start the server_controller first, and then the ui.
    server_controller.start()
    ui_logic.start()


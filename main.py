
# TODO implement logger
# TODO implement config parser


from server.server_controller import SocketServerController
from server.server_communicator import SocketCommunicator


if __name__ == "__main__":
    server = SocketCommunicator(9000)
    server_controller = SocketServerController(server)
    server_controller.start()


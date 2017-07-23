
# TODO implement logger
# TODO implement config parser


from server.server_controller import ServerController
from server.server_communicator import TunnelServerCommunicator


if __name__ == "__main__":
    server = TunnelServerCommunicator(9000)
    server_controller = ServerController(server)
    server_controller.start()


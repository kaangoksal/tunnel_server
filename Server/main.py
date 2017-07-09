
# TODO implement logger
# TODO implement config parser


from Server.server_controller import ServerController
from Server.server import TunnelServer


if __name__ == "__main__":
    server = TunnelServer(9000)
    server_controller = ServerController(server)
    server_controller.start()


from Client.client_controller import ClientController
from Client.client import Client


if __name__ == '__main__':
    client = Client(9000, "localhost", "device-1", "password-1")
    client_controller = ClientController(client)
    client_controller.run()
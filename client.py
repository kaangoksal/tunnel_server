import os
import socket
import time
import signal
import sys
import struct
import json
import threading
from queue import Queue

from reverse_ssh_task import ReverseSSHTask
lock = threading.Lock()



#TODO Implement logger

# Received messages will be inserted to this que so others can process them
received_queue = Queue()

# Messages that are scheduled to send will be inserted to this que so comms can send them
will_send_queue = Queue()



class Client(object):

    def __init__(self, port, host, username, password):
        #self.serverHost = 'localhost'
        self.serverHost = host
        self.serverPort = port
        self.socket = None
        self.username = username
        self.password = password
        # This is a crappy way to put it here... CS 2340 game weak
        self.running_processes = {}

    def register_signal_handler(self):
        signal.signal(signal.SIGINT, self.quit_gracefully)
        signal.signal(signal.SIGTERM, self.quit_gracefully)
        return

    def quit_gracefully(self, signal=None, frame=None):
        print('\nQuitting gracefully')
        if self.socket:
            try:
                self.socket.shutdown(2)
                self.socket.close()
            except Exception as e:
                print('Could not close connection %s' % str(e))
                # continue
        sys.exit(0)
        return

    def socket_create(self):
        """ Create a socket """
        try:
            self.socket = socket.socket()
        except socket.error as e:
            print("Socket creation error" + str(e))
            return
        return

    def socket_connect(self):
        """ Connect to a remote socket """
        try:
            self.socket.connect((self.serverHost, self.serverPort))
        except socket.error as e:
            print("Socket connection error: " + str(e))
            time.sleep(5)
            raise
        try:
            return_dict = {'username': self.username, 'password': self.password, 'hostname': socket.gethostname()}
            return_string = json.dumps(return_dict, sort_keys=True, indent=4, separators=(',', ': '))
            print(return_string)
            self.send_message(return_string)
        except socket.error as e:
            print("Cannot send hostname to server: " + str(e))
            raise
        return

    def print_output(self, output_str):
        """ Prints command output """
        sent_message = str.encode(output_str + str(os.getcwd()) + '> ')
        self.socket.send(struct.pack('>I', len(sent_message)) + sent_message)
        print(output_str)
        return

    def send_message(self, output_str):
        """ Sends message to the server
         :param output_str: string message that will go to the server
        """
        print("will send this " + str(output_str))
        byte_array_message = str.encode(output_str)
        #We are packing the lenght of the packet to unsigned big endian struct to make sure that it is always constant length
        self.socket.send(struct.pack('>I', len(byte_array_message)) + byte_array_message)

        return
    def read_message(self):
        """ Read message length and unpack it into an integer
        """
        raw_msglen = self._recvall(self.socket, 4)
        print("First blocking call here!")
        if not raw_msglen:
            return None
        # We are unpacking a big endian struct which includes the length of the packet, struct makes sure that the header
        # which includes the length is always 4 bytes in length. '>I' indicates that the struct is a unsigned integer big endian
        # CS2110 game strong
        print("Received message, will process it " +str(raw_msglen))
        msglen = struct.unpack('>I', raw_msglen)[0]
        # Read the message data
        return self._recvall(self.socket, msglen)

    @staticmethod
    def _recvall(conn, n):
        """ Helper function to recv n bytes or return None if EOF is hit
        :param n: length of the packet
        :param conn: socket to read from
        """
        data = b''
        while len(data) < n:
            packet = conn.recv(n - len(data))
            #packet = conn.recv(4096)
            if not packet:
                return None
            data += packet
        #print("Debug recvall " + str(data))
        return data




def inbox_work(client):
    #TODO optimize blocking
    while 1:

        print("Will read message! ")
        received_message = client.read_message()

        if received_message is not None and received_message != b'':
            json_package = received_message.decode("utf-8")
            try:
                json_package = json.loads(json_package)
                payload = json_package["payload"]
                type = json_package["type"]

                received_queue.put(("server", type , payload))
            except Exception as e:
                print("Received impropper message " + str(e) + " message was " + str(received_message))
        else:
            print("comms received unexpected " + str(received_message) )


def outbox_work(client):
    #TODO optimize blocking
    if will_send_queue.not_empty:
        #print("Attempting to send message")
        message = will_send_queue.get()
        client.send_message(message)
        #print("Sent message")
    else:
        time.sleep(0.1)
    #print("Finished reading and sending")

def main_logic(client):
    while 1:
        if received_queue.not_empty:
            message_block = received_queue.get()

            sender, type_of_message, message = message_block
            # print("Main Logic Reporting! Sender " + str(sender) + " type_of_message " + type_of_message + " message " + message)
            if type_of_message == "action":
                if message == "SSH-Start":
                    print("Firing the ssh tunnel!")

                    key_location ="/home/kaan/Desktop/centree-clientsupervisor/ssh_server_key"
                    server_addr = "umb.kaangoksal.com"
                    server_username = "ssh_server"

                    reverse_ssh_job = ReverseSSHTask("main_server_reverse_ssh","started", key_location, server_addr, server_username, 22, 7000)
                    reverse_ssh_job.start_connection()

                    client.running_processes["SSH"] = reverse_ssh_job

                elif message == "SSH-Stop":
                    print("Stopping the ssh tunnel!")
                    reverse_ssh_job = client.running_processes["SSH"]

                    print(reverse_ssh_job.stop_connection())

            else:
                print("Message received! " + str(message))


def initialize_threads(client):

    # This thread receives messages from the server
    receive_thread = threading.Thread(target=inbox_work, args=(client,))
    receive_thread.setName("Receive Thread")
    receive_thread.start()

    # This thread sends messages to the server
    send_thread = threading.Thread(target=outbox_work, args=(client,))
    send_thread.setName("Send Thread")
    send_thread.start()

    # This thread listens to the received messages and does stuff according to them
    logic_thread = threading.Thread(target=main_logic, args=(client,))
    logic_thread.setName("Logic Thread")
    logic_thread.start()


def main():
    # TODO read a config file
    # SSH server config
    # Tunnel Server config
    # self identity

    client = Client(9000, "localhost", "device-1", "password-1")
    client.register_signal_handler()
    client.socket_create()
    while True:
        try:
            client.socket_connect()
        except Exception as e:
            print("Error on socket connections: %s" %str(e))
            time.sleep(5)
        else:
            break
    try:
        initialize_threads(client)

    except Exception as e:
        print('Error in main: ' + str(e))
    print("Amigos I go")
    # client.socket.close()
    return


if __name__ == '__main__':
    # while True:
    main()

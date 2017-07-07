import os
import socket
import subprocess
import time
import signal
import sys
import struct

import threading

lock = threading.Lock()

"""
one thread for talking with the server
one thread for executing tasks from the server


"""


from queue import Queue

import json

#TODO Implement logger

#Received messages will be inserted to this que so others can process them
received_queue = Queue()

#Messages that are scheduled to send will be inserted to this que so comms can send them
will_send_queue = Queue()



class Client(object):

    def __init__(self, port, host, username, password):
        #self.serverHost = 'localhost'
        self.serverHost = host
        self.serverPort = port
        self.socket = None
        self.username = username
        self.password = password

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


    def continuous_msg(self):
        while 1:

            self.send_message("AHmed")
            time.sleep(1)



def comms(client):
    while 1:

        print("Will read message! ")
        received_message = client.read_message()

        if received_message is not None and received_message != b'':
            received_message = received_message.decode("utf-8")
            received_queue.put(("server", "message", received_message))
        else:
            print("comms received weird " + str(received_message) )

        # raw_msglen = client.socket.recv(4)
        # print(raw_msglen)
        # print(client.socket.recv(7))


        if will_send_queue.not_empty:
            print("Attempting to send message")
            message = will_send_queue.get()
            client.send_message(message)
            print("Sent message")
        else:
            time.sleep(0.1)
        print("Finished reading and sending")

def main_logic(client):
    while 1:
        if received_queue.not_empty:
            message_block = received_queue.get()

            sender, type_of_message, message = message_block

            if type_of_message is "action":
                if message is "SSH":
                    print("Firing the ssh tunnel!")
                    while 1:
                        time.sleep(10)
            else:
                print("Message received! " + str(message))

def initialize_threads(client):
    comms_thread = threading.Thread(target=comms, args=(client,))
    comms_thread.setName("Communication Thread")
    comms_thread.start()

    logic_thread = threading.Thread(target=main_logic, args=(client,))
    logic_thread.setName("Logic Thread")
    logic_thread.start()


def main():
    #TODO read a config file
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
    #client.socket.close()
    return


if __name__ == '__main__':
    # while True:
    main()

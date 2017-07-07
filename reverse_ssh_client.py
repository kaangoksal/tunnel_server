
import os
import socket
import subprocess
import time
import signal
import sys
import struct


# command = ["ssh", "-N", "-R",  "1999:localhost:22", "-i", "/home/kaan/Desktop/centree-clientsupervisor/ssh_server_key", "ssh_server@umb.kaangoksal.com"]

command = "ssh -N -R 7000:localhost:22 -i /home/kaan/Desktop/centree-clientsupervisor/ssh_server_key ssh_server@umb.kaangoksal.com"


cmd = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, stdin=subprocess.PIPE)

print(cmd.poll())
# output_bytes = cmd.stdout.read() + cmd.stderr.read()
# output_str = output_bytes.decode("utf-8", errors="replace")
# print(cmd.poll())

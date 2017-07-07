

import subprocess
import time
import os
import signal

"""
How does this shit work?
Well... good question.

When the command gets executed, a reverse ssh tunnel is created to the server at umb.kaangoksal.com
starting at the port 7000 on the server and at 22 on the client (the computer which executes this code)
-N allows us to not to start a ssh shell to the remote pc, if you remove that it will ssh into ssh_server@umb.kaangoksal.com

The ssh_server user is a non sudo user, therefore even you access the server with that account you cant do much. (This will also be patched...)





To start the reverse ssh thing, I have used the default ssh server/client, running on linux machines. This is the best way to make sure that it is secure.
The shell command for reverse ssh is executed with subprocess and then it can be killed with os.killpg(os.getpgid(cmd.pid), signnal.SIGTERM). However you need to
start the process in a way that it will take down the child process created by the command. When subprocess command executes, two processes start

kaan     20155 20154  0 13:00 ?        00:00:00 /bin/sh -c ssh -N -R 7000:localhost:22 -i /home/kaan/Desktop/centree-clientsupervisor/ssh_server_key ssh_server@umb.kaangoksal.com
kaan     20156 20155  0 13:00 ?        00:00:00 ssh -N -R 7000:localhost:22 -i /home/kaan/Desktop/centree-clientsupervisor/ssh_server_key ssh_server@umb.kaangoksal.com

you might kill one of them but if the other one is not killed (with the pid 20155) the reverse ssh connection will be left open!


Sources:
https://stackoverflow.com/questions/4789837/how-to-terminate-a-python-subprocess-launched-with-shell-true/4791612#4791612




"""

# command = ["ssh", "-N", "-R",  "1999:localhost:22", "-i", "/home/kaan/Desktop/centree-clientsupervisor/ssh_server_key", "ssh_server@umb.kaangoksal.com"]



command = "ssh -N -R 7000:localhost:22 -i /home/kaan/Desktop/centree-clientsupervisor/ssh_server_key ssh_server@umb.kaangoksal.com"


cmd = subprocess.Popen(command, stdout=subprocess.PIPE,
                       shell=True, preexec_fn=os.setsid)

print(cmd.poll())
print(cmd.pid)
time.sleep(5)
os.killpg(os.getpgid(cmd.pid), signal.SIGTERM)
time.sleep(5)
print(cmd.poll())

# output_bytes = cmd.stdout.read() + cmd.stderr.read()
# output_str = output_bytes.decode("utf-8", errors="replace")
# print(cmd.poll())

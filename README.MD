The main server is server.py  
It handles client connections, reads their messages and sends them messages from the user  

clients have tasks, such as  
- reverse ssh  
- gstreamer  
- software update  
these are executed in different subprocesses. 

The reverse SSH Task requires a user account on the server called ssh_server 
Please make sure that it is not a sudo user and shell is disabled for the clients connecting for ssh to that user.

the server needs to have the public key of the clients  
and the operator needs to know the username and the password for the clients (username is sent but the password will be predefined)  



Version History

V 0.0.1

- Added new commands for ssh stop
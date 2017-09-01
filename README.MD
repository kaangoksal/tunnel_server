The main server is server.py  
It handles client connections, reads their messages and sends them messages from the user  

clients have tasks, such as  
- reverse ssh  
- live video
- software update  
these are executed in different subprocesses. 

The reverse SSH Task requires a user account on the server called ssh_server 
Please make sure that it is not a sudo user and shell is disabled for the clients connecting for ssh to that user.

the server needs to have the public key of the clients  
and the operator needs to know the username and the password for the clients (username is sent but the password will be predefined)  



**Version History**  

Stuff to be implemented  
- Database for authentication, and event logging  
- Notification sender (to notify admins realtime)  
- Log retrieval, automatic software updater
- Live video start
- Logs for individual clients


V 0.0.14 

- Implemented logger  
- Implemented thread watchdog which will bring the crashed threads to life  


V 0.0.13

- socket connection will be terminated if the client does not reply the ping requests
- improved agility furhter, client logic is seperated from the actual server code.
- there is only one ping thread now
- added thread info to gui


V 0.0.12

- added safe-guards for empty byte array storms.
- optimized for cpu spikes, select blocks until there is a message


V 0.0.1

- Added new commands for ssh stop

The Server
=========

`server.py` file includes the server communication logic where it talks to the client, reads messages, 
sends messages and accepts connections.   

`server_controller.py` uses the methods from server.py and operates the server, it runs threads to start send and receive process,
routes messages internally and provides a simple UI so that the user can start ssh process.  

`main.py` is the main method that fires everything.



**Self reflection on the structure**  
There can be another layer after the server controller for the logic of the code to increase the agility of the system. Rigth now the UI stuff is done
in the server_controller file which is not that smart. 

**Self reflection on performance**  
The server.py needs to fire new threads dynamically for each client connected, right now two threads check all the sockets for incoming and outgoing messages.

**Self reflection on security**  
There is no encryption or authentication present on the system, which is a big problem.


**Configuration**  
The server machine which is going to run the server code needs to have a non sudo  user account that will allow ssh tunnels. 
The shell access for the connecting client can be disabled with the options that will be in authorized_users file. The user account can be named
ssh_server, and it will accept the client tunnels with the key files.  

a box will have a ssh key and it will open a reverse ssh tunnel to ssh_server@backend.centree.xyz, it will provide keys to the server so that server can authenticate.




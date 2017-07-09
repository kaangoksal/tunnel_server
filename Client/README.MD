The Client
=========


`client.py` includes all the communication logic and also the client logic, It is not a good implementation. 
The client can execute certain tasks. Tasks are located in tasks folder. Each has their own class since they might have different
requirements and functionality. However in future they might get revised in a better structure.


**Self reflection on the structure**  
The communication section and the logic must be refactored to different files. 

**Self reflection on performance**  
Since the client is only talking to the server, there is not much to improve in terms of that. However at the moment, threads require a little bit
of optimization, they consume a good deal of cpu.

**Self reflection on security**  
the client username and password will be stored in open, even though the home folder is encrypted (will be), we might looks for better options. 
The tunnel communication has no encryption, that is bad... 


**Configuration**  
There is not much to configure except generating a reverse ssh key for the server and placing it with the appropriate security options (no shell access).





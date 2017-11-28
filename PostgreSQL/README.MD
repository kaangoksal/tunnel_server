**Installation**

PostgreSQL

sudo apt-get update
sudo apt-get install postgresql postgresql-contrib



**Usage**
 Login to postgresql  
 psql  
 sudo su - postgres  
 
 Create a new user  
 CREATE ROLE patrick WITH LOGIN PASSWORD '12345';
 ALTER USER 'user_name' WITH PASSWORD 'new_password';
 
 
 Shows Users  
 \du  
 Shows Databases  
 \l   

Create Database
CREATE DATABASE campusbuzz;

GRANT ALL PRIVILEGES ON DATABASE campusbuzz TO patrcik;

Connect to a database
\connect campusbuzz

shows the location of the configuration files
SHOW config_file;



Restarts the postgresql
sudo service postgresql restart  

psql -U master -h  campusbuzz.cijlnph9mqin.us-east-1.rds.amazonaws.com -p 5432 postgres

show tables
\dt




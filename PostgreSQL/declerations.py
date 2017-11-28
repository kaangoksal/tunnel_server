
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

postgresql_username = 'tunnel_server_user'
postgresql_password = "hell_wid_goga"
postgresql_host = 'localhost'
database_name = "tunnel_server_db"

engine = create_engine('postgresql://' + postgresql_username + ':' + postgresql_password + '@' + postgresql_host + '/' +
                       database_name)

Base = declarative_base()

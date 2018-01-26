
# TODO implement logger
# TODO implement config parser

import logging
from logging import handlers as logging_handlers

from handlers.message_handler import MessageHandler
from handlers.utility_handler import UtilityHandler
from logic.server_logic import ServerLogic
from core.server_controller import SocketServerController
from core.server_socket_layer import ServerSocketLayer

from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker

from PostgreSQL.core_database_models import User
from PostgreSQL.declerations import Base
from PostgreSQL.declerations import engine



# new_user = Users("username1", "superpass2", "test device", "botnet")
# session.add(new_user)
# session.commit()



def create_logger():
    server_logger = logging.getLogger(__name__)
    server_logger.setLevel(logging.DEBUG)
    # handlers = logging.FileHandler('core.log')
    handler = logging_handlers.TimedRotatingFileHandler('core.log', when='midnight', interval=1, backupCount=7,
                                                        utc=True)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    server_logger.addHandler(handler)
    return server_logger

def connect_database():
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


if __name__ == "__main__":
    # Socket communicator is for talking with the clients
    db_session = connect_database()

    new_logger = create_logger()

    server = ServerSocketLayer(9000,  logger=new_logger)
    # Server controller pings receives and sends messages and checks on the clients

    message_handler = MessageHandler()
    utility_handler = UtilityHandler()
    message_handler.register_handler(utility_handler, "utility")

    server_controller = SocketServerController(server, message_handler, db_session, logger=new_logger)

    # core logic is the ui which allows us to create and send commands to the clients and also see info about them!
    ui_logic = ServerLogic()
    ui_logic.server_controller = server_controller
    #we start the server_controller first, and then the ui.
    ui_logic.start()
    server_controller.start()




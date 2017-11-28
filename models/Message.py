"""
This library is for storing parsing and transporting messages in an organized way.

Author: Kaan Goksal
9th of JULY in the year of 2017

"""
import datetime
import json
from enum import Enum


class Message(object):

    """
    {
        "payload": "{\"utility_type\": \"PING\"}",
        "sender": "server",
        "to": "floatingPi",
        "type": "utility"
    }


    """

    def __init__(self, sender, to, message_type, payload):
        self.sender = sender
        self.to = to
        self.type = message_type
        self.payload = payload
        self.date = datetime.datetime.now()
        self.receive_date = None

    def __str__(self):
        return "Message Block with Sender: " + str(self.sender) + " To: " + str(self.to) + " type: " + str(self.type) + " payload: " + str(self.payload)

    def pack_to_json_string(self):
        """
        This method is used to pack message into a json string for sending to someother client.
        :return: Json String representation of a message
        """
        return_dict = {
            "sender": self.sender,
            "to": self.to,
            "type": self.type.value,
            "payload": json.dumps(self.payload),
            "date": str(self.date)
                       }
        return_string = json.dumps(return_dict, sort_keys=True, indent=4, separators=(',', ': '))
        return return_string

    @staticmethod
    def json_string_to_message(json_string):
        """
        This method is used to parse from string to message, this should be used while a message is coming from a client.

        :param json_string: Message in string format
        :return: Message object
        """
        json_package = json.loads(json_string)

        payload = json.loads(json_package["payload"])

        message_type = MessageType[json_package["type"]]

        to = json_package["to"]
        sender = json_package["sender"]
        return_message = Message(sender, to, message_type, payload)

        if "date" in json_package:
            date = datetime.datetime.strptime(json_package["date"], '%Y-%m-%d %H:%M:%S.%f')
            return_message.date = date
        return_message.receive_date = datetime.datetime.now()

        return return_message


class MessageType(Enum):
    def __str__(self):
        return str(self.value)

    utility = "utility"
    communication = "communication"
    action = "action"
    event = "event"



import json


class Message(object):

    def __init__(self, sender, to, type, payload):
        self.sender = sender
        self.to = to
        self.type = type
        self.payload = payload

    def __str__(self):
        return "Message Block with Sender: " + str(self.sender) + " To: " + str(self.to) + " type: " + str(type) + " payload: " + str(self.payload)

    def pack_to_json_string(self):
        return_dict = {
            "sender": self.sender,
            "to": self.to,
            "type": self.type,
            "payload": self.payload
                       }
        return_string = json.dumps(return_dict, sort_keys=True, indent=4, separators=(',', ': '))
        return return_string

    @staticmethod
    def json_string_to_message(json_string):
        json_package = json.loads(json_string)
        payload = json_package["payload"]
        message_type = json_package["type"]
        to = json_package["to"]
        sender = json_package["sender"]
        return Message(sender, to, message_type, payload)

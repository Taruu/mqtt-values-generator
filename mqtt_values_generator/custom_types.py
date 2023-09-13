import json
import time
import uuid
from typing import Union

value_range = r"([+-]?(?=\.\d|\d)(?:\d+)?(?:\.?\d*))(?:[Ee]([+-]?\d+))?@([+-]?(?=\.\d|\d)(?:\d+)?(?:\.?\d*))(?:[Ee]([+-]?\d+))?"
random_value_list = r"(?<=@)-?\d+(\.\d+)?(?=@)"


class Message:
    def __init__(self, topic: str, value: Union[str, int, float, list, dict]):
        self.topic = topic
        self.value = value
        pass

    def get(self):
        if isinstance(self.value, dict):
            payload = self.value
        else:
            payload = {'read': {'value': self.value}}

        return {'topic': self.topic, 'payload': json.dumps({'read': payload}), 'qos': 1, 'retain': False,
                'properties': {"User Property": {'message_id': uuid.uuid1().__str__()}}}

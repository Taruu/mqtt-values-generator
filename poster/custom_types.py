import json
import time
from typing import Union


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
                'properties': {"User Property": {'timestamp': time.time()}}}

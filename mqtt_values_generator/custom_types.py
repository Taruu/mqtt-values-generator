import json
import random
import re
import time
import uuid
from json import JSONEncoder
from typing import Union

range_value_regex = r"(-?\d+(?:\.\d+)?)R(-?\d+(?:\.\d+)?)"
choose_value_regex = r'(-?\d+\.\d+|-?\d+\b)@'


# subclass JSONEncoder
class ToJsonEncoder(JSONEncoder):
    def default(self, o):
        return o.to_json()


class NumberGenerator:
    """Используем в случае если нам нужно"""

    def __init__(self, value: str):
        self.generator = None
        range_value = re.fullmatch(range_value_regex, value)
        if range_value:
            self.generator = self.random_range(range_value[1], range_value[2])
        choose_list = re.findall(choose_value_regex, value)
        if choose_list:
            self.generator = self.random_choose(choose_list)

    @staticmethod
    def random_range(start: float, end: float):
        while True:
            value = random.uniform(float(start), float(end))
            yield float("{:.4f}".format(value))

    @staticmethod
    def random_choose(values: list):
        while True:
            yield float(random.choice(values))

    def __next__(self):
        return next(self.generator)

    def to_json(self):
        return self.__next__()


def find_paths_to_replace(data, current_path=[]):
    paths = []
    if isinstance(data, dict):
        for key, value in data.items():
            new_path = current_path + [key]
            paths.extend(find_paths_to_replace(value, new_path))
    elif isinstance(data, str):
        choose_list = re.findall(choose_value_regex, data)
        range_value = re.fullmatch(range_value_regex, data)
        if (len(choose_list) > 0) or range_value:
            paths.append(current_path)

    return paths


class Message:
    """Сообщение для отправки"""

    def __init__(self, topic: str, value: Union[str, int, float, list, dict]):
        self.topic = topic
        self.value = value

        if isinstance(self.value, dict):
            convert_to_generator = find_paths_to_replace(self.value)
            for path_list in convert_to_generator:
                iter_path = path_list
                dict_value = self.value
                while len(iter_path) > 1:
                    key = iter_path.pop(0)
                    dict_value = dict_value[key]
                key = iter_path.pop()
                dict_value[key] = NumberGenerator(dict_value[key])
        else:
            self.value = {'value': self.value}

    def get(self):

        return {'topic': self.topic, 'payload': json.dumps({'read': self.value}, cls=ToJsonEncoder),
                'qos': 1, 'retain': False,
                'properties': {"User Property": {'message_id': uuid.uuid1().__str__()}}}

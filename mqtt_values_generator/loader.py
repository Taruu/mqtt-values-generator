import asyncio
import json
import uuid
from asyncio import AbstractEventLoop
from typing import Union

from mqtt_values_generator.custom_types import Message, NumberGenerator
from mqtt_values_generator.paho_local.mqtt.publish import multiple
from loguru import logger


def iter_paths(d):
    def iter1(d, path):
        paths = []
        for k, v in d.items():
            if isinstance(v, dict):
                paths += iter1(v, path + [k])
            paths.append((path + [k], v))
        return paths

    return iter1(d, [])


class CalculateWorker:
    def __init__(self, to_calculate: dict):
        self.values = {}
        self.expression = {}

        # To ideal variant dont need use this check
        # for key in self.calculated.keys():
        #     intersection_count = 0
        #     for key_to_check in self.calculated.keys():
        #         if key in key_to_check:
        #             intersection_count += 1
        #     if intersection_count > 1:
        #         text = f"calculated: {key} intersect with other meanings"
        #         raise ValueError(text)

        for key, value in to_calculate.items():
            if type(value) in [int, float]:
                self.values.update({key: value})
            elif any([True if letter in value else False for letter in "R@"]):
                self.values.update({key: NumberGenerator(value)})
            elif any(
                    [True if letter in value else False for letter in "+-/*^"]):
                self.expression.update({key: value})
            else:
                error_text = f"value {key} not correct"
                raise ValueError(error_text)

    def _calc(self, key: str):
        value: str = self.expression.get(key)
        value = value.strip()
        list_values = value.split(' ')
        eval_list = []
        for value in list_values:
            if (value in self.values) or (value in self.expression):
                eval_list.append(self.get(value))
            else:
                eval_list.append(value)

        eval_string = " ".join(
            [str(value_to_str) for value_to_str in eval_list])
        return eval(eval_string)

    def get(self, key: str) -> Union[int, float]:
        if key in self.values:
            value = self.values.get(key)
            if type(value) is NumberGenerator:
                return value.get_last()
            return value
        elif key in self.expression:
            return self._calc(key)
        else:
            return None

    def __next__(self):
        # take next random values
        for value in self.values.values():
            if type(value) is NumberGenerator:
                next(value)


class MessageWorker:
    def __init__(self, config_file_path: str, host='localhost', port=1883):
        self._task_work = None
        self.task = None
        self.host = host
        self.port = port
        self.calculated_worker = CalculateWorker({})

        with open(config_file_path, 'r') as file:
            file_lines = file.read()
            file_config = json.loads(file_lines)

        config_paths = iter_paths(file_config)
        # TODO add support path without 'value'
        config_paths = list(
            filter(lambda path: isinstance(path[1], dict), config_paths))

        logger.info(f"""Load config from: \t {config_file_path}""")
        logger.debug(f"Load {len(config_paths)} parameters")

        post_messages_configs = list(
            filter(
                lambda path: len(path[0]) == 1 and path[0] == ['SYS'],
                config_paths))[-1][-1]

        if "host" in post_messages_configs:  # Получаем хостинг
            self.host = post_messages_configs.get('host')
            logger.debug(f"Set host from config: {self.host}")

        if 'port' in post_messages_configs:
            self.port = post_messages_configs.get('port')
            logger.debug(f"Set port from config: {self.host}")

        self.repeat_time = post_messages_configs.get('repeat_time')
        self.keepalive = post_messages_configs.get('keepalive')

        self.calculated: dict = post_messages_configs.get('calculated')

        if self.calculated:
            self.calculated_worker = CalculateWorker(self.calculated)

        messages_list = list(filter(lambda path: 'values' in path[1]
                                                 or 'value' in path[1],
                                    config_paths))

        self.message_list: list[Message] = []

        for path, values in messages_list:
            temp_values: dict = values.get('values')

            if not temp_values:
                temp_values = values.get('value')

            # Фильтр от вложенных данных
            if isinstance(temp_values, dict):
                temp_values.pop('values', None)
                temp_values.pop('value', None)

            topic = "/".join(path)
            values = temp_values
            self.message_list.append(
                Message(topic, values, calculate_worker=self.calculated_worker))
        logger.info(
            f"Load {len(self.message_list)} values from {config_file_path}")

    def get_task(self, loop: AbstractEventLoop):
        self._task_work = True
        self.task = loop.create_task(self.post_messages())
        return self.task

    def __del__(self):
        self._task_work = False

    async def post_messages(self):
        while self._task_work:
            prepared_messages = [message.get() for message in self.message_list]
            client_id = uuid.uuid4().__str__()
            multiple(prepared_messages,
                     hostname=self.host, port=self.port,
                     keepalive=self.keepalive,
                     client_id=client_id)
            logger.info(f"[{client_id}] Post {len(prepared_messages)} messages")

            next(self.calculated_worker)
            await asyncio.sleep(self.repeat_time)

import asyncio
import json
import uuid
from asyncio import AbstractEventLoop

from poster.custom_types import Message
from paho_local.mqtt.publish import multiple


def iter_paths(d):
    def iter1(d, path):
        paths = []
        for k, v in d.items():
            if isinstance(v, dict):
                paths += iter1(v, path + [k])
            paths.append((path + [k], v))
        return paths

    return iter1(d, [])


class MessageWorker:
    def __init__(self, config_file_path: str, host="localhost", port=1883):
        self._task_work = None
        self.task = None
        self.host = host
        self.port = port

        with open(config_file_path, 'r') as file:
            file_lines = file.read()
            file_config = json.loads(file_lines)

        config_paths = iter_paths(file_config)
        config_paths = list(filter(lambda path: isinstance(path[1], dict), config_paths))

        post_messages_configs = list(
            filter(
                lambda path: len(path[0]) == 1 and path[0] == ['SYS'],
                config_paths))[-1][-1]

        if "host" in post_messages_configs:
            self.host = post_messages_configs.get('host')
        if 'port' in post_messages_configs:
            self.port = post_messages_configs.get('port')

        self.repeat_time = post_messages_configs.get('repeat_time')
        self.keepalive = post_messages_configs.get('keepalive')

        messages_list = list(filter(lambda path: 'values' in path[1]
                                                 or 'value' in path[1], config_paths))

        self.message_list: list[Message] = []
        for path, values in messages_list:
            temp_values: dict = values.get('values')
            if not temp_values:
                temp_values = values.get('value')

            if isinstance(temp_values, dict):
                temp_values.pop('values', None)
                temp_values.pop('value', None)

            topic = "/".join(path)
            values = temp_values
            self.message_list.append(Message(topic, values))
            print(topic, values)

    def get_task(self, loop: AbstractEventLoop):
        self._task_work = True
        self.task = loop.create_task(self.post_messages())
        return self.task

    def __del__(self):
        self._task_work = False

    async def post_messages(self):
        while self._task_work:
            prepared_messages = [message.get() for message in self.message_list]
            print(prepared_messages)
            multiple(prepared_messages,
                     hostname=self.host, port=self.port, keepalive=self.keepalive,
                     client_id=uuid.uuid4().__str__())
            await asyncio.sleep(self.repeat_time)

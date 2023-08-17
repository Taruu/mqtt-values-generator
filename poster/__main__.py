# values = Properties(PacketTypes.PUBLISH)
# values.__setattr__("UserProperty", [("a", "1"), ("b", "2")])
# print(type(values))
#
# msgs = [{'topic': "paho_local/test/multiple", 'payload': "multiple 1", 'properties': values},
#         {'topic': "paho_local/test/multiple", 'payload': "multiple 42",
#          'properties': {'UserProperty': [('a', '0'), ('b', '0')]}},
#         ("paho_local/test/multiple", "multiple 2", 0, False)]
#
# multiple(msgs, protocol=paho.mqtt.client.MQTTv5, will={'topic': "paho_local/test/multiple", 'payload': "0 1", 'properties': values})
import asyncio

from loader import MessageWorker

worker = MessageWorker('/home/taruu/PycharmProjects/mqtt-values-generator/configs/config_example.json')

loop = asyncio.get_event_loop()
task = worker.get_task(loop)
asyncio.gather(task)
loop.run_forever()

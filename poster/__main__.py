import paho.mqtt.client

from paho_local.mqtt.publish import multiple

from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes

values = Properties(PacketTypes.PUBLISH)
values.__setattr__("UserProperty", [("a", "1"), ("b", "2")])
print(type(values))

msgs = [{'topic': "paho_local/test/multiple", 'payload': "multiple 1", 'properties': values},
        {'topic': "paho_local/test/multiple", 'payload': "multiple 42",
         'properties': {'UserProperty': [('a', '0'), ('b', '0')]}},
        ("paho_local/test/multiple", "multiple 2", 0, False)]

multiple(msgs, protocol=paho.mqtt.client.MQTTv5)

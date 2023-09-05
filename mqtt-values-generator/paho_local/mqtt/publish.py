import collections
from types import NoneType
from typing import Iterable

import paho
from paho import mqtt
from paho.mqtt.client import MQTTv311, MQTTv5
from loguru import logger
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.properties import Properties


def _do_properties(message):
    """Make Properties form dict"""
    temp_properties_dict = None
    if isinstance(message, dict):
        temp_properties_dict = message.get('properties')

    elif isinstance(message, (tuple, list)):
        if len(message) == 5:
            temp_properties_dict = message[-1]
    else:
        raise TypeError('message must be a dict, tuple, or list')

    if not (isinstance(temp_properties_dict, (dict, Properties, NoneType))):
        raise TypeError('properties must be a dict or None')

    if isinstance(temp_properties_dict, dict):
        # _send_publish use PUBLISH value
        temp_properties = Properties(PacketTypes.PUBLISH)
        for key, value in temp_properties_dict.items():
            if isinstance(value, dict):
                for key_value, value_data in value.items():
                    temp_properties.__setattr__(key, (str(key_value), str(value_data)))
        message.update({'properties': temp_properties})
    return message


def _do_publish(client):
    """Internal function"""

    message = client._userdata.popleft()

    _do_properties(message)

    if isinstance(message, dict):
        client.publish(**message)
    elif isinstance(message, (tuple, list)):
        client.publish(*message)


def _on_connect(client, userdata, flags, rc):
    """Internal callback"""
    # pylint: disable=invalid-name, unused-argument

    if rc == 0:
        if len(userdata) > 0:
            _do_publish(client)
    else:
        raise mqtt.MQTTException(paho.connack_string(rc))


def _on_connect_v5(client, userdata, flags, rc, properties):
    """Internal v5 callback"""
    _on_connect(client, userdata, flags, rc)


def _on_publish(client, userdata, mid):
    """Internal callback"""
    # pylint: disable=unused-argument

    if len(userdata) == 0:
        client.disconnect()
    else:
        _do_publish(client)


def multiple(msgs, hostname="localhost", port=1883, client_id="", keepalive=60,
             will=None, auth=None, tls=None, protocol=MQTTv5,
             transport="tcp", proxy_args=None):
    """Publish multiple messages to a broker, then disconnect cleanly.

    This function creates an MQTT client, connects to a broker and publishes a
    list of messages. Once the messages have been delivered, it disconnects
    cleanly from the broker.

    msgs : a list of messages to publish. Each message is either a dict or a
           tuple.

           If a dict, only the topic must be present. Default values will be
           used for any missing arguments. The dict must be of the form:

           msg = {'topic':"<topic>", 'payload':"<payload>", 'qos':<qos>,
           'retain':<retain>, 'userdata' : <userdata>}
           topic must be present and may not be empty.
           If payload is "", None or not present then a zero length payload
           will be published.
           If qos is not present, the default of 0 is used.
           If retain is not present, the default of False is used.

           If a tuple, then it must be of the form:
           ("<topic>", "<payload>", qos, retain, userdata)

    hostname : a string containing the address of the broker to connect to.
               Defaults to localhost.

    port : the port to connect to the broker on. Defaults to 1883.

    client_id : the MQTT client id to use. If "" or None, the Paho library will
                generate a client id automatically.

    keepalive : the keepalive timeout value for the client. Defaults to 60
                seconds.

    will : a dict containing will parameters for the client: will = {'topic':
           "<topic>", 'payload':"<payload">, 'qos':<qos>, 'retain':<retain>}.
           Topic is required, all other parameters are optional and will
           default to None, 0 and False respectively.
           Defaults to None, which indicates no will should be used.

    auth : a dict containing authentication parameters for the client:
           auth = {'username':"<username>", 'password':"<password>"}
           Username is required, password is optional and will default to None
           if not provided.
           Defaults to None, which indicates no authentication is to be used.

    tls : a dict containing TLS configuration parameters for the client:
          dict = {'ca_certs':"<ca_certs>", 'certfile':"<certfile>",
          'keyfile':"<keyfile>", 'tls_version':"<tls_version>",
          'ciphers':"<ciphers">, 'insecure':"<bool>"}
          ca_certs is required, all other parameters are optional and will
          default to None if not provided, which results in the client using
          the default behaviour - see the paho_local.mqtt.client documentation.
          Alternatively, tls input can be an SSLContext object, which will be
          processed using the tls_set_context method.
          Defaults to None, which indicates that TLS should not be used.

    transport : set to "tcp" to use the default setting of transport which is
          raw TCP. Set to "websockets" to use WebSockets as the transport.
    proxy_args: a dictionary that will be given to the client.
    """

    if not isinstance(msgs, Iterable):
        raise TypeError('msgs must be an iterable')

    client = paho.mqtt.client.Client(client_id=client_id, userdata=collections.deque(msgs),
                                     protocol=protocol, transport=transport)

    client.on_publish = _on_publish
    if protocol == mqtt.client.MQTTv5:
        client.on_connect = _on_connect_v5
    else:
        client.on_connect = _on_connect

    if proxy_args is not None:
        client.proxy_set(**proxy_args)

    if auth:
        username = auth.get('username')
        if username:
            password = auth.get('password')
            client.username_pw_set(username, password)
        else:
            raise KeyError("The 'username' key was not found, this is "
                           "required for auth")

    if will is not None:
        _do_properties(will)
        client.will_set(**will)

    if tls is not None:
        if isinstance(tls, dict):
            insecure = tls.pop('insecure', False)
            client.tls_set(**tls)
            if insecure:
                # Must be set *after* the `client.tls_set()` call since it sets
                # up the SSL context that `client.tls_insecure_set` alters.
                client.tls_insecure_set(insecure)
        else:
            # Assume input is SSLContext object
            client.tls_set_context(tls)

    client.connect(hostname, port, keepalive)
    client.loop_forever()


def single(topic, payload=None, qos=0, retain=False, hostname="localhost",
           port=1883, properties=None, client_id="", keepalive=60, will=None,
           auth=None,
           tls=None, protocol=MQTTv5, transport="tcp", proxy_args=None):
    """Publish a single message to a broker, then disconnect cleanly.

    This function creates an MQTT client, connects to a broker and publishes a
    single message. Once the message has been delivered, it disconnects cleanly
    from the broker.

    topic : the only required argument must be the topic string to which the
            payload will be published.

    payload : the payload to be published. If "" or None, a zero length payload
              will be published.

    qos : the qos to use when publishing,  default to 0.

    retain : set the message to be retained (True) or not (False).

    hostname : a string containing the address of the broker to connect to.
               Defaults to localhost.

    port : the port to connect to the broker on. Defaults to 1883.

    properties : a dict or Properties class.
                 can be presented like dict with allowed Properties values.

    client_id : the MQTT client id to use. If "" or None, the Paho library will
                generate a client id automatically.

    keepalive : the keepalive timeout value for the client. Defaults to 60
                seconds.

    will : a dict containing will parameters for the client: will = {'topic':
           "<topic>", 'payload':"<payload">, 'qos':<qos>, 'retain':<retain>,
           'properties' : <properties>}.
           Topic is required, all other parameters are optional and will
           default to None, 0 and False respectively.
           Defaults to None, which indicates no will should be used.
           Properties not necessary. Can be a dict or Properties class

    auth : a dict containing authentication parameters for the client:
           auth = {'username':"<username>", 'password':"<password>"}
           Username is required, password is optional and will default to None
           if not provided.
           Defaults to None, which indicates no authentication is to be used.

    tls : a dict containing TLS configuration parameters for the client:
          dict = {'ca_certs':"<ca_certs>", 'certfile':"<certfile>",
          'keyfile':"<keyfile>", 'tls_version':"<tls_version>",
          'ciphers':"<ciphers">, 'insecure':"<bool>"}
          ca_certs is required, all other parameters are optional and will
          default to None if not provided, which results in the client using
          the default behaviour - see the paho.mqtt.client documentation.
          Defaults to None, which indicates that TLS should not be used.
          Alternatively, tls input can be an SSLContext object, which will be
          processed using the tls_set_context method.

    transport : set to "tcp" to use the default setting of transport which is
          raw TCP. Set to "websockets" to use WebSockets as the transport.
    proxy_args: a dictionary that will be given to the client.
    """

    msg = {'topic': topic, 'payload': payload, 'qos': qos, 'retain': retain,
           'properties': properties}

    multiple([msg], hostname, port, client_id, keepalive, will, auth, tls,
             protocol, transport, proxy_args)

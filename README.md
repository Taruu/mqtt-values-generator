# mqtt-values-generator

Simple console-like app for generate mqtt messages form config


# How to install:

Start run a mqtt broker, for exsmaple mosquitto:

https://mosquitto.org/download/

after create a python venv

```bash
python3 -m venv venv
source venv/bin/activate
pip3 install git+https://github.com/Taruu/mqtt-values-generator
```

And after you can run a program:

```
wget https://github.com/Taruu/mqtt-values-generator/raw/main/configs/config_example.json -O config.json

mqtt-values-generator
```

For the program to work you need to be in your venv environment


You can lookup messages in next app:
https://mqttx.app/


# About config.json

You can check config_example.json in configs folder in repo.
config file has next feaches:

**SYS**:
- repeat_time - how often to send messages
- keepalive - mqtt message lifetime
- calculated - calculated fields

All other fields are considered paths to the topic
- values - field list data in one message
- value - one field of data to one topic 

also you can use string macros:

**Random range**:
- `-100R100` - value between -100 and 100
- `42.000R42.999` - value random with decimal accuracy

**Choose**:
- `100@200@300@` - take ranom value from list

Set calculated value:
- `@V00|value_result` - take calculated value from *SYS* and set in field.
- `@Vvalue_1` - take calculated value from *SYS* without format (take like integer value)

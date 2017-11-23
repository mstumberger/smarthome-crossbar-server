#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2014 Roger Light <roger@atchoo.org>
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Distribution License v1.0
# which accompanies this distribution.
#
# The Eclipse Distribution License is available at
#   http://www.eclipse.org/org/documents/edl-v10.php.
#
# Contributors:
#    Roger Light - initial implementation

# This shows an example of using the publish.single helper function.

#import context  # Ensures paho is in PYTHONPATH
import paho.mqtt.publish as publish
import json
import random
topic = 'register'


#publish.single("mqtt/esp32", json.dumps({"mac": "hbdsao", "temperature": random.randint(18, 34),
#                                        "humidity": random.randint(18, 34)}), hostname="localhost", port=1883)
#publish.single('initialize/30aea40ec2ac', 'RELAY', hostname="192.168.88.247", port=1883)

publish.single('initialize/30aea40ec2ac', json.dumps({"sensor": 'I2C_DISPLAY', "new": True, "pins": {"GPIO": [4, 5]}}), hostname="192.168.88.247", port=1883)

#publish.single('initialize/30aea40ec2ac', json.dumps({"sensor": 'LED', "new": True}), hostname="192.168.88.247", port=1883)

publish.single('initialize/30aea40ec2ac', json.dumps({"sensor": 'TEMP_DH11', "new": True, "pins": {"GPIO": 26}}), hostname="192.168.88.247", port=1883)

# publish.single('initialize/30aea40ec2ac', json.dumps({"sensor": 'TEMP_DALLAS', "new": True}), hostname="192.168.88.247", port=1883)

#publish.single('initialize/30aea40ec2ac', json.dumps({"sensor": 'HUMIDITY_SENSOR', "new": True}), hostname="192.168.88.247", port=1883)

#publish.single('initialize/30aea40ec2ac', json.dumps({"sensor": 'RELAY', "new": True}), hostname="192.168.88.247", port=1883)
#
# import time
# time.sleep(2)
#
# for i in range(1, 9):
#     print(i)
#     jsn = {"channel": i, "value": "toggle", "sensor": "RELAY"}
#     publish.single('esp32/relay/30aea40ec2ac', json.dumps(jsn), hostname="192.168.88.247", port=1883)
#     #print("published")
#     time.sleep(0.2)

#!/usr/bin/python
# -*- coding: utf-8 -*-
#  #############################  #
# #    *  Service CLIENT  *     # #
# #         ~~~~~~~~~~~         # #
# #  company: Na zvezi d.o.o.   # #
# #  author: Marko Stumberger   # #
# sudo pip install twisted-mqtt
#  #############################  #
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from autobahn.twisted.util import sleep
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredList
from twisted.internet.error import ReactorNotRunning
from twisted.internet.endpoints import clientFromString
from twisted.internet import reactor
from twisted_mqtt import MQTTService
from mqtt.client.factory import MQTTFactory
import os
import logging as log
import txaio
import json
txaio.use_twisted()

BROKER = "tcp:localhost:1883"


class Component(ApplicationSession):
    mqtt = None
    protocol = None

    @inlineCallbacks
    def onJoin(self, details):
        # create a new database connection pool. connections are created lazy (as needed)
        print("CONNECTED")
        self.mqtt = MQTTService(self, clientFromString(reactor, BROKER), MQTTFactory(profile=MQTTFactory.PUBLISHER | MQTTFactory.SUBSCRIBER), BROKER)

        yield self.subscribe(self.printmsg, u"server_update")
        yield self.register(self.mqtt_publish, u"mqtt_publish")
        print str(details.session)
        self.call(u"add_service", str(details.session),
                                  "forwarder",
                                  "CORE",
                                  "localhost")
        #self.mqtt.subscribe_to("topic")

    def mqtt_subscribe(self, topic):
        self.mqtt.subscribe_to(topic)
        return "Subscribed to topic: {}".format(topic)

    @inlineCallbacks
    def printmsg(self, topic, data):
        print(topic)
        if topic == "register/relay":
            print("Register relay device")

            response = yield self.call(u"register_relay_client", str(data))
            print(response)
        elif topic == "register/device":
            print("Register device")

            response = yield self.call(u"register_device", str(data))
            print(response)

        elif "initialize/" in topic:
            print(topic, data, "from forwarder")

        elif topic == "register/sensor" or topic == "register/temp":
            print("Register sensor")

            response = yield self.call(u"register_client", str(data))
            print(response)

        elif topic == "alerts":
            print("GOT ALERT")
            self.publish(u"alerts", b"ALO NE MORES DIHAT")

        elif topic == "measurements":
            response = yield self.call(u"insert", str(data))
            print(response)
        else:
            print("Unknown topic: {}".format(topic))

    def mqtt_publish(self, topic, data):
        print(data)
        try:
            self.mqtt.publish(topic, bytes(data))
        except ValueError as e:
            print(e)
        return "Published"

    def onDisconnect(self):
        log.info("Client was shutdown")

if __name__ == '__main__':
    txaio.start_logging(level='info')
    runner = ApplicationRunner(url=u"ws://localhost:8080/ws", realm=u"realm1")
    try:
        runner.run(Component, auto_reconnect=True)
    except Exception as e:
        print("Server is offline", e)
        pass

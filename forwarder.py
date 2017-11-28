#!/usr/bin/python
# -*- coding: utf-8 -*-
#  #############################  #
#     -----------------------     #
#     MQTT Forwarder Service      #
#     ------------------------    #
# #  author: Marko Stumberger   # #
# sudo pip install twisted-mqtt   #
#  #############################  #

from autobahn.twisted.wamp import ApplicationSession
from twisted.internet.defer import inlineCallbacks, DeferredList
from twisted.application.internet import ClientService, backoffPolicy
from twisted.internet.endpoints import clientFromString
from twisted.internet import reactor
from mqtt.client.factory import MQTTFactory
BROKER = "tcp:localhost:1883"


class MQTTService(ClientService):

    def __init__(self, mainApp, endpoint, factory, BROKER):
        ClientService.__init__(self, endpoint, factory, retryPolicy=backoffPolicy())
        self.BROKER = BROKER
        self.mainApp = mainApp
        self.protocol = None
        self.startService()

    def startService(self):
        print("starting MQTT Client Subscriber Service")
        self.whenConnected().addCallback(self.connectToBroker)
        ClientService.startService(self)

    @inlineCallbacks
    def connectToBroker(self, protocol):
        self.protocol = protocol
        self.protocol.onPublish = self.onPublish
        self.protocol.onDisconnection = self.onDisconnection
        self.protocol.setWindowSize(6)
        try:
            yield self.protocol.connect("Forwarder", keepalive=60)
            yield self.subscribe()

        except Exception as e:
            print("Connecting to {broker} raised {excp!s}".format(broker=self.BROKER, excp=e))
        else:
            print("Connected and subscribed to {broker}".format(broker=self.BROKER))

    def publish(self, topic, message):

        def _logFailure(failure):
            print("publisher reported {message}".format(message=failure.getErrorMessage()))
            return failure

        d1 = self.protocol.publish(topic=topic, qos=1, message=message)
        d1.addErrback(_logFailure)
        return d1

    def subscribe(self):
        def _logFailure(failure):
            print("reported {message}".format(message=failure.getErrorMessage()))
            return failure

        def _logGrantedQoS(value):
            print("response {value!r}".format(value=value))
            return True

        def _logAll(*args):
            print("all subscriptions complete args={args!r}".format(args=args))

        d1 = self.protocol.subscribe("mqtt/esp32", 1)
        d1.addCallbacks(_logGrantedQoS, _logFailure)
        d2 = self.protocol.subscribe("register/#", 2)
        d2.addCallbacks(_logGrantedQoS, _logFailure)
        d3 = self.protocol.subscribe("measurements", 1)
        d3.addCallbacks(_logGrantedQoS, _logFailure)
        d4 = self.protocol.subscribe("alerts", 2)
        d4.addCallbacks(_logGrantedQoS, _logFailure)
        d5 = self.protocol.subscribe("initialize/#", 2)
        d5.addCallbacks(_logGrantedQoS, _logFailure)
        d6 = self.protocol.subscribe("update", 2)
        d6.addCallbacks(_logGrantedQoS, _logFailure)

        dlist = DeferredList([d1, d2, d3, d4, d5], consumeErrors=True)
        dlist.addCallback(_logAll)
        return dlist

    def subscribe_to(self, topic):
        def _logFailure(failure):
            print("subscriber reported {message}".format(message=failure.getErrorMessage()))
            return failure

        def _logGrantedQoS(value):
            print("subscriber response {value!r}".format(value=value))
            return True

        d1 = self.protocol.subscribe(topic, 1)
        d1.addCallbacks(_logGrantedQoS, _logFailure)
        return d1

    def onPublish(self, topic, payload, qos, dup, retain, msgId):
        self.mainApp.printmsg(topic, payload)

    def onDisconnection(self, reason):
        print(" >< Connection was lost ! ><, reason={r}".format(r=reason))


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
        print("Client was shutdown")
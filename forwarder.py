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
from twisted.internet.defer import inlineCallbacks, DeferredList, returnValue
from twisted.application.internet import ClientService, backoffPolicy
from twisted.internet.endpoints import clientFromString
from twisted.internet import reactor
from mqtt.client.factory import MQTTFactory

host = "localhost"


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
            return failure

        def _logGrantedQoS(value):
            return True

        def _logAll(*args):
            print("all subscriptions complete args={args!r}".format(args=args))

        d1 = self.protocol.subscribe("initialize/#", 1)
        d1.addCallbacks(_logGrantedQoS, _logFailure)
        d2 = self.protocol.subscribe("register/#", 2)
        d2.addCallbacks(_logGrantedQoS, _logFailure)
        d3 = self.protocol.subscribe("actions/#", 1)
        d3.addCallbacks(_logGrantedQoS, _logFailure)
        d4 = self.protocol.subscribe("measurements/#", 2)
        d4.addCallbacks(_logGrantedQoS, _logFailure)
        d5 = self.protocol.subscribe("alerts", 2)
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
        self.mainApp.mqtt_receives(topic, payload)

    def onDisconnection(self, reason):
        print(" >< Connection was lost ! ><, reason={r}".format(r=reason))


class Component(ApplicationSession):
    mqtt = None
    protocol = None

    @inlineCallbacks
    def onJoin(self, details):
        # create a new database connection pool. connections are created lazy (as needed)
        print("CONNECTED")
        broker = "tcp:{}:1883".format(host)
        self.mqtt = MQTTService(self, clientFromString(reactor, broker), MQTTFactory(profile=MQTTFactory.PUBLISHER | MQTTFactory.SUBSCRIBER), broker)

        yield self.register(self.mqtt_publish, u"mqtt_publish")
        self.call(u"add_service", str(details.session),
                                  "forwarder",
                                  "CORE",
                                  "localhost")
        # self.mqtt.subscribe_to("topic")

    def mqtt_subscribe(self, topic):
        self.mqtt.subscribe_to(topic)
        return "Subscribed to topic: {}".format(topic)

    @inlineCallbacks
    def mqtt_receives(self, topic, data):
        response = yield self.call(u"mqtt_receives", topic, data)
        returnValue("ok")
        return

    def mqtt_publish(self, topic, data):
        print(data)
        try:
            self.mqtt.publish(topic, bytes(data))
        except ValueError as e:
            print(e)
        return "Published"

    def onDisconnect(self):
        print("Client was shutdown")


if __name__ == '__main__':
    from autobahn.twisted.wamp import ApplicationRunner
    runner = ApplicationRunner(url=u"ws://{}:8080/ws".format(host), realm=u"realm1")
    try:
        runner.run(Component, auto_reconnect=True)
    except Exception as e:
        print("Server is offline", e)
        pass

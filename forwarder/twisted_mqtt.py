# -----------------------
# MQTT Subscriber Service
# ------------------------
from twisted.internet.defer import inlineCallbacks, DeferredList
from twisted.application.internet import ClientService, backoffPolicy


class MQTTService(ClientService):

    def __init__(self, mainApp, endpoint, factory, BROKER):
        ClientService.__init__(self, endpoint, factory, retryPolicy=backoffPolicy())
        self.BROKER = BROKER
        self.mainApp = mainApp
        self.startService()

    def startService(self):
        print("starting MQTT Client Subscriber Service")
        # invoke whenConnected() inherited method
        self.whenConnected().addCallback(self.connectToBroker)
        ClientService.startService(self)

    @inlineCallbacks
    def connectToBroker(self, protocol):
        '''
        Connect to MQTT broker
        '''
        self.protocol                 = protocol
        self.protocol.onPublish       = self.onPublish
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
        '''
        Callback Receiving messages from publisher
        '''
        #print("topic: {}, message: {}".format(topic, payload))
        #print topic, payload.split(",")[1]
        self.mainApp.printmsg(topic, payload)

    def onDisconnection(self, reason):
        '''
        get notfied of disconnections
        and get a deferred for a new protocol object (next retry)
        '''
        print(" >< Connection was lost ! ><, reason={r}".format(r=reason))
        #self.mainApp.printmsg(" >< Connection was lost ! ><, reason={r}".format(r=reason))
        #self.whenConnected().addCallback(self.connectToBroker)

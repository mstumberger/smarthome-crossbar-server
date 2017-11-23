from twisted.internet.defer import inlineCallbacks
from autobahn.twisted.wamp import ApplicationSession
from autobahn.wamp.types import SubscribeOptions, RegisterOptions, CallOptions
from autobahn.twisted.util import sleep
from pprint import pprint
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
import sys
import os
import json

version = "1.0.1"

RPC_COUNTER = {}
# List of devices
DEVICES = {'mac': None, 'sensor_id': None}

# List of uninitialized devices
uninitialized_devices = []

# List of active services, key is service name
class AppSession(ApplicationSession):
    con = None
    cur = None
    forwarder_msg_timestamp = datetime.now()
    forwarder_timestamp = datetime.now()
    services = {}
    services_sessions = {}

    def on_session_leave(self, session_details):
        session_details = str(session_details)
        
        print("to delete", session_details)

        try:
            self.services.pop(self.services_sessions[session_details], "")
            print("deleted service")
        except KeyError:
            print "error service"
        try:
            self.services_sessions.pop(session_details, "")
            print("deleted session")
        except KeyError:
            print "error session"
        self.forwarder_timestamp = datetime.now()

    def conncet_to_db(self):
        try:
            self.con = psycopg2.connect(database="CBS_DB",
                                   user="postgres",
                                   password="supertemp",
                                   host="192.168.88.254")
            self.con.autocommit = True
            self.cur = self.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            self.log.info("!!! Connected to DB !!!")

        except psycopg2.OperationalError:
            print("Can't connect to database"), sys.exc_info()

    def get_devices(self, details=None):
        global DEVICES
        self.cur.execute("SELECT id, device_name, mac_addr as mac, location, sensor_id, details, client_id from devices_id")
        db_devices = self.cur.fetchall()
        DEVICES = {}
        if db_devices:
            for db_device in db_devices:
                if db_device['id'] and db_device['mac'] and db_device['sensor_id']:
                    DEVICES[db_device['id']] = {}
                    DEVICES[db_device['id']]['mac'] = db_device['mac']
                    DEVICES[db_device['id']]['sensor_id'] = db_device['sensor_id']
                    DEVICES[db_device['id']]['device_name'] = db_device['device_name']
                    DEVICES[db_device['id']]['details'] = db_device['details']
                    DEVICES[db_device['id']]['location'] = db_device['location']
                    DEVICES[db_device['id']]['client_id'] = db_device['client_id']
        return DEVICES

    def sensors_on_devices(self, details=None):
        self.cur.execute("SELECT id, device_name, mac_addr as mac, location, sensor_id, details, client_id from devices_id")
        db_devices = self.cur.fetchall()
        temp_DEVICES = {}
        if db_devices:
            for db_device in db_devices:
                if db_device['id'] and db_device['mac'] and db_device['sensor_id']:

                    if db_device['client_id'] not in temp_DEVICES:
                        temp_DEVICES[db_device['client_id']] = {}
                    if db_device['id'] not in temp_DEVICES[db_device['client_id']]:
                        temp_DEVICES[db_device['client_id']][db_device['id']] = {}

                    temp_DEVICES[db_device['client_id']][db_device['id']]['mac'] = db_device['mac']
                    temp_DEVICES[db_device['client_id']][db_device['id']]['sensor_id'] = db_device['sensor_id']
                    temp_DEVICES[db_device['client_id']][db_device['id']]['device_name'] = db_device['device_name']
                    temp_DEVICES[db_device['client_id']][db_device['id']]['details'] = db_device['details']
                    temp_DEVICES[db_device['client_id']][db_device['id']]['location'] = db_device['location']
                    temp_DEVICES[db_device['client_id']][db_device['id']]['client_id'] = db_device['client_id']
        return temp_DEVICES


    def return_uninitialized_devices(self, details=None):
        return uninitialized_devices

    def register_device(self, client_hw_id, details=None):
        for device in DEVICES:
            if client_hw_id == DEVICES[device]['client_id']:
                print("Send config", DEVICES[device]['sensor_id'])
                self.call(u"mqtt_publish", "initialize/{}".format(DEVICES[device]['client_id']),
                          json.dumps({"sensor": DEVICES[device]['sensor_id'], "new": False, "pins": DEVICES[device]['details']}))

        else:
            if client_hw_id not in uninitialized_devices:
                uninitialized_devices.append(client_hw_id)
            print("Device not found, initialize device on topic initialize/{}!".format(client_hw_id))
            return "False"

    def register_relay_client(self, data, details=None):
        print(data)
        data = json.loads(str(data))
        device_id = None
        print(uninitialized_devices)
        for device in DEVICES:
            if unicode(DEVICES[device]['mac']) == data["mac"] and unicode(DEVICES[device]['sensor_id']) == data["sensor_id"]:
                print("GOT DEVICE")
                device_id = device
                print(DEVICES[device_id]['details'])
                self.call(u"mqtt_publish", "initialize/{}".format(DEVICES[device_id]['client_id']),
                          json.dumps({"sensor": DEVICES[device_id]['sensor_id'], "new": False}))
                print("Device is already registered, id: {}".format(device_id))
                return "Device is already registered, id: {}".format(device_id)
        if not device_id:
            try:
                self.cur.execute(
                    "INSERT INTO devices_id (device_name, ip, mac_addr, active, sensor_id, details, client_id) VALUES (%s, %s, %s, %s, %s, %s, %s) returning id",
                    (data["client_id"], data["ip"], data['mac'], 'TRUE', data["sensor_id"], json.dumps(data["pins"]), data["client_id"]))
                device_id = self.cur.fetchone()
                print(device_id)
                self.get_devices()
                print("New device was added to database with id: {}".format(device_id))
                return "New device was added to database with id: {}".format(device_id)
            except TypeError as e:
                print(e)
                device_id = 0
                print("{} {}".format(sys.exc_info()[2].tb_lineno, sys.exc_info()))
                return "{} {}".format(sys.exc_info()[2].tb_lineno, sys.exc_info())

    def save_relay_details(self, data, device_id, details=None):
        pprint(data)
        print(device_id)
        return "OK"

    def register_client(self, data, details=None):
        print(data)
        data = json.loads(str(data))
        device_id = None
        for device in DEVICES:
            if unicode(DEVICES[device]['mac']) == data["mac"] and unicode(DEVICES[device]['sensor_id']) == data["sensor_id"]:
                print("GOT DEVICE")
                device_id = device
                print(DEVICES[device_id]['details'])

                print("Device is already registered, id: {}".format(device_id))
                return "Device is already registered, id: {}".format(device_id)
        if not device_id:
            try:
                self.cur.execute(
                    "INSERT INTO devices_id (device_name, ip, mac_addr, active, sensor_id, details, client_id) VALUES (%s, %s, %s, %s, %s, %s, %s) returning id",
                    (data["sensor_id"], data["ip"], data['mac'], 'TRUE', data["sensor_id"], json.dumps(data["pins"]), data["client_id"]))
                device_id = self.cur.fetchone()['id']
                print(device_id)
            except TypeError as e:
                print(e)
                print("{} {}".format(sys.exc_info()[2].tb_lineno, sys.exc_info()))
                return "{} {}".format(sys.exc_info()[2].tb_lineno, sys.exc_info())
        return "Done"

    def insert_value(self, data, details=None):
        global DEVICES
        data = json.loads(str(data))
        try:
            device_id = None
            for device in DEVICES:
                if unicode(DEVICES[device]['mac']) == data["mac"] and unicode(DEVICES[device]['sensor_id']) == data["sensor_id"]:
                    device_id = device
            if not device_id:
                try:
                    self.cur.execute(
                        "INSERT INTO devices_id (device_name, ip, mac_addr, active, sensor_id) VALUES (%s, %s, %s, %s, %s) returning id",
                        ('ESP32', data["ip"], data['mac'], 'TRUE', data["sensor_id"]))
                    device_id = self.cur.fetchone()['id']
                    print(device_id)
                    self.get_devices()
                except TypeError as e:
                    print(e)
                    device_id = 0
                    print("{} {}".format(sys.exc_info()[2].tb_lineno, sys.exc_info()))
            try:
                jsn = dict()
                try:
                    jsn["temperature"] = data["temperature"]
                except:
                    pass
                try:
                    jsn["humidity"] = data["humidity"]
                except:
                    pass
                try:
                    jsn["carbon_dioxid"] = data["carbon_dioxid"]
                except:
                    pass
                self.cur.execute(
                    "INSERT INTO measurements (timestamp, event, measurement, device_id) VALUES (%s, %s, %s, %s)",
                    ('now()', data["sensor_id"], json.dumps(jsn), device_id))
            except TypeError as e:
                print(e)
                print("{} {}".format(sys.exc_info()[2].tb_lineno, sys.exc_info()))

            # db("""INSERT INTO temperature_readings (timestamp, event, measurement) VALUES (now(), 'temp', json""")
            print("INSERTED INTO DATABASE")
            return "INSERTED INTO DATABASE"
        except Exception as e:
            print("{} {}".format(sys.exc_info()[2].tb_lineno, sys.exc_info()))
            return "FAIL"

    def add_service(self, session, service, service_type, ip, details=None):
        if service not in self.services:
            self.services[service] = {'available': True, 'client': service, 'ip': ip,
                                 'version': version, 'type': service_type, 'session': session}
            self.services_sessions[session] = service
            print("Added service {} to list".format(service))

    # RELAY switching
    def switch_relay(self, device_id, channel, details=None):
        self.call(u"mqtt_publish", "esp32/relay/{}".format(DEVICES[device_id]['device_name']), json.dumps({"channel": channel, "value": "toggle"}))
        DEVICES[device_id]['details'][unicode(channel)][u'state'] = not DEVICES[device_id]['details'][unicode(channel)][u'state']
        print(DEVICES[device_id]['details'][unicode(channel)][u'state'])
        print(DEVICES[device_id]['details'][unicode(channel)])
        #self.cur.execute("""UPDATE devices_id SET details = jsonb_set(details, '{"%s"}', '{"GPIO": 16, "name": "%s", "state": false}');""", (device_id, channel))

        return "OK"

    def print_pubsub(self, data, details=None):
        print(data)

    @inlineCallbacks
    def onJoin(self, details):
        # DataBase connection settings
        self.conncet_to_db()
        self.get_devices()
        # Register options
        options = RegisterOptions(details_arg=str('details'))

        yield self.register(self.insert_value, u'insert', options=options)
        yield self.register(self.register_device, u'register_device', options=options)
        yield self.register(self.register_relay_client, u'register_relay_client', options=options)
        yield self.register(self.register_client, u'register_client', options=options)
        yield self.register(self.switch_relay, u'relay', options=options)
        yield self.register(self.get_devices, u'get_devices', options=options)
        yield self.register(self.sensors_on_devices, u'sensors_on_devices', options=options)
        yield self.register(self.save_relay_details, u'save_relay_details', options=options)
        yield self.register(self.return_uninitialized_devices, u'return_uninitialized_devices', options=options)
        yield self.register(self.add_service, u'add_service', options=options)
        #yield self.subscribe(self.print_pubsub, u'alerts')
        yield self.subscribe(self.on_session_leave, u'wamp.session.on_leave')

        print("all procedures registered")
        
        while True:
            if 'forwarder' not in self.services:
                if datetime.now() >= self.forwarder_msg_timestamp:
                    print("FORWARDER IS OFFLINE FOR {}".format(str(datetime.now()-self.forwarder_timestamp).split(".")[0]))
                    self.forwarder_msg_timestamp += timedelta(seconds=5)
                    
            yield sleep(2)

os.system("crossbar start")

# SmartHome server (0.2): 

## TODO:

- [ ] Make forwarder as a service that only forwards messages from mqtt to backend
- [ ] Make raspberry pi mqtt client
- [ ] Make client component, that uses raspberry client code listening on mqtt protocol
- [ ] Add update raspberry pi client to flask app

># Install python dependencies:
>
    sudo apt-get -y install build-essential libssl-dev libffi-dev \
    libreadline-dev libbz2-dev libsqlite3-dev libncurses5-dev

    sudo apt-get install python3-dev
    or
    sudo apt-get install python-dev

    pip3 install -r requirements.txt
>

># Install postgres:
>
    sudo apt-get install postgresql postgresql-contrib
>
>### Create database:
>
    CREATE TABLE devices_id (
    id serial primary key,
    device_name character varying(30) DEFAULT NULL::character varying,
    ip character varying(30) DEFAULT NULL::character varying,
    mac_addr character varying(30) DEFAULT NULL::character varying,
    location character varying(30),
    active boolean,
    sensor_id character varying(30),
    client_id character varying(30),
    details jsonb
    );
>
    CREATE TABLE measurements (
    "timestamp" timestamp with time zone,
    event character varying(30),
    measurement jsonb,
    device_id integer
    );
>
>
>



># Connect to server:
    domain:8080 (ws, http)
    domain:8181 (wss, https) (in future)
    domain:1883 (mqtt)

># Curl format:
>
>## With args:
>
    curl -H "Content-Type: application/json" -d '{"procedure": "PROCEDURE_NAME", "args": ["args", "args"]}' domain:8080/caller
>
>## Without args:
>
    curl -H "Content-Type: application/json" -d '{"procedure": "PROCEDURE_NAME"}' domain:8080/caller
>
># Send webhook that will post in topic "webhook":
>
    curl -H "Content-Type: text/plain" -d 'fresh webhooks!' http://domain:8080/webhook
> 
># Send msg to any topic (publisher):
>
    curl -H "Content-Type: application/json" -d '{"topic": "logs", "args": ["Hello, world"]}' http://domain:8080/publish
> 
>
># Get micropython code (code repository):
>
    http://domain:8080/code/main.py
> 
>
># Webhook url ( git webhook ):
>
    http://domain:8080/git_webhook
> 
>

# SmartHome server (0.2): 
># Install python dependencies:
>
    pip3 install -r requirements.txt
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

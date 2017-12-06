from flask import Flask, request, send_from_directory
import json
from pprint import pprint
import os, shutil
import git
import pickle

if not os.path.exists("auto_update.p"):
    auto_update = {"backend": True,
                   "frontend": True,
                   "esp_client": True,
                   "raspberry_client": True}

    pickle.dump(auto_update, open("auto_update.p", "wb"))
else:
    auto_update = pickle.load( open("auto_update.p", "rb"))

print auto_update
"""
http://gitpython.readthedocs.io/en/stable/tutorial.html?highlight=clone
"""
app = Flask(__name__, static_url_path='')


@app.route('/frontend_webhook', methods=['POST'])
def frontend_webhook():
    if auto_update["frontend"]:
        pprint(request.data)
        data = request.data.strip().replace("\n", "")
        repository = json.loads(data)["repository"]["links"]["html"]["href"].split("/")
        git_path = "git@{}:{}/{}".format(repository[2], repository[3], repository[4])
        print("GIT: {}".format(git_path))
    else:
        print("Frontend Webhook is disabled in auto_update.p config")
    return "OK"


@app.route('/backend_webhook', methods=['POST'])
def backend_webhook():
    if auto_update["backend"]:
        pprint(request.data)
        data = request.data.strip().replace("\n", "")
        repository = json.loads(data)["repository"]["links"]["html"]["href"].split("/")
        git_path = "git@{}:{}/{}".format(repository[2], repository[3], repository[4])
        print("GIT: {}".format(git_path))
    else:
        print("Backend Webhook is disabled in auto_update.p config")
    return "OK"


@app.route('/esp_client_webhook', methods=['POST'])
def esp_client_webhook():
    if auto_update["esp_client"]:
        pprint(request.data)
        data = request.data.strip().replace("\n", "")
        repository = json.loads(data)["repository"]["links"]["html"]["href"].split("/")
        git_path = "git@{}:{}/{}".format(repository[2], repository[3], repository[4])
        print("GIT: {}".format(git_path))
    else:
        print("ESP client Webhook is disabled in auto_update.p config")
    return "OK"


@app.route('/raspberry_client_webhook', methods=['POST'])
def raspberry_client_webhook():
    if auto_update["raspberry_client"]:
        pprint(request.data)
        data = request.data.strip().replace("\n", "")
        repository = json.loads(data)["repository"]["links"]["html"]["href"].split("/")
        git_path = "git@{}:{}/{}".format(repository[2], repository[3], repository[4])
        print("GIT: {}".format(git_path))
    else:
        print("Raspberry client Webhook is disabled in auto_update.p config")
    return "OK"


@app.route('/repository/<path:path>')
def repository(path):
    print("File {} was downloaded.".format(path))
    return send_from_directory('../', path)


@app.route("/")
def root():
    return "<h1>Hello, This is a Flask app!</h1>" \
           "<h2>it's used as auto updater for all source code of the project SmartHome<br></h2>" \
           "/app/frontend_webhook<br>" \
           "/app/backend_webhook<br>" \
           "/app/esp_client_webhook<br>" \
           "/app/raspberry_client_webhook<br>" \
           "/app/repository/<br>"


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)

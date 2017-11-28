from flask import Flask, request, send_from_directory
import json
from pprint import pprint
import os, shutil
import git
import pickle
auto_update = pickle.load(open("auto_update.p", "rb"))

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


@app.route('/backend_webhook', methods=['POST'])
def backend_webhook():
    if auto_update["backend"]:
        pprint(request.data)
        data = request.data.strip().replace("\n", "")
        repository = json.loads(data)["repository"]["links"]["html"]["href"].split("/")
        git_path = "git@{}:{}/{}".format(repository[2], repository[3], repository[4])
        print("GIT: {}".format(git_path))

    else:
        print("Frontend Webhook is disabled in auto_update.p config")


@app.route('/esp_client_webhook', methods=['POST'])
def esp_client_webhook():
    if auto_update["esp_client"]:
        pprint(request.data)
        data = request.data.strip().replace("\n", "")
        repository = json.loads(data)["repository"]["links"]["html"]["href"].split("/")
        git_path = "git@{}:{}/{}".format(repository[2], repository[3], repository[4])
        print("GIT: {}".format(git_path))

    else:
        print("Frontend Webhook is disabled in auto_update.p config")


@app.route('/repository/<path:path>')
def repository(path):
    return send_from_directory('../smarthome-esp32-client', path)


@app.route("/")
def hello():
    return "Hello World!"


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8282)
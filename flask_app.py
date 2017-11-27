from flask import Flask, request, send_from_directory
import json
from pprint import pprint
import os, shutil
import git

"""
http://gitpython.readthedocs.io/en/stable/tutorial.html?highlight=clone
"""
app = Flask(__name__, static_url_path='')


@app.route('/git_webhook', methods=['POST'])
def root():
    try:
        data = json.loads(request.data)
        print "New commit by: {}".format(data['commits'][0]['author']['name'])
        pprint(data)
        print "New commit by: {}".format(data['repository']['url'])
        data["project"]["namespace"] = data["project"]["namespace"].replace(" ", "_")
        data["project"]["name"] = data["project"]["name"].replace(" ", "_")
        src = str(os.path.join("RSYNC_REPO", data["project"]["namespace"], data["project"]["namespace"] + "_" + data["project"]["name"] + "_" + data["checkout_sha"]))
        if not os.path.exists(src):
           os.makedirs(src)
        else:
            shutil.rmtree(src)
            os.makedirs(src)
        try:
            git.Git().clone(data['repository']['url'], src)
        except Exception as e:
            print "path seems to exists.", e

        destination = str(os.path.join("RSYNC_REPO", data["project"]["namespace"], data["project"]["name"]+"_LATEST"))

        if not os.path.exists(destination):
            os.makedirs(destination)
        else:
            shutil.rmtree(destination)
            shutil.copytree(src, destination, True)
        return "OK"
    except:
        return "FAIL"


@app.route('/code/<path:path>')
def send_js(path):
    return send_from_directory('web', path)
# def file():
#     return app.send_static_file('web/main.py')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8282)
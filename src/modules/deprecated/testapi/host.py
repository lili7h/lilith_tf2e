import json
import time

from flask import Flask, jsonify
import random

app = Flask(__name__)


@app.route("/mac/events/v1", methods=['GET'])
def dummy_events():
    time.sleep(random.randint(a=7, b=16))
    return jsonify({
        "test_response": "lilith is hot"
    })


@app.route("/mac/game/v1", methods=['GET'])
def dummy_game():
    with open('/src/modules/deprecated/testapi/test_jsons/game.json', 'r') as h:
        _json = h.read()
    return _json


@app.route("/", methods=['GET'])
def tld():
    return "<h1> Hello baby </h1>"

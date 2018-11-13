#!/usr/bin/env python
from flask import Flask, request, jsonify
from pprint import pprint
import json

app = Flask(__name__)


@app.route('/', methods=['GET'])
def webhook():

    hello_text = "Hello, World!"

    return jsonify(hello_text)

app.run(host='0.0.0.0', port=5000, debug=True)

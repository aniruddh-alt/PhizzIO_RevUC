from flask import Flask, request, jsonify
import json
import requests
import os
import sys
import time
import datetime
import random
import string
import re
import base64
import hashlib
import hmac

from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return "Welcome to the Flask backend!"

if __name__ == "__main__":
    app.run(debug=True)



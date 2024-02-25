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
import psycopg2

app = Flask(__name__)

# Database connection details
DATABASE_URL = 'postgresql://your_username:your_password@localhost:5432/your_database_name'


def connect_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


from flask import Flask, request, jsonify
import psycopg2

app = Flask(__name__)

# Database connection details (replace with your values)
DATABASE_URL = 'postgresql://postgres:l1RFqY5YNx1ZqtUM@org-phizzio-inst-phizzio-standard.data-1.use1.tembo.io:5432/postgres'

def connect_db():
    return psycopg2.connect(DATABASE_URL)

# Signup route
@app.route('/signup', methods=['POST'])
def signup():
    username = request.json.get('username')
    password = request.json.get('password')

    # Validate input (add checks for username and password strength)

    with connect_db() as conn:
        with conn.cursor() as cur:
            # Hash the password for security
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
        conn.commit()

    return jsonify({'message': 'Signup successful'}), 201

# Login route
@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')

    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT password FROM users WHERE username = %s", (username,))
            hashed_password = cur.fetchone()

            if hashed_password and hashed_password[0] == hashlib.sha256(password.encode()).hexdigest():
                return jsonify({'message': 'Login successful'}), 200
            else:
                return jsonify({'error': 'Invalid username or password'}), 401

# Other routes and database interactions
# ...

if __name__ == "__main__":
    app.run(debug=True)

def fetch_data():
    conn = connect_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM your_table_name")
        data = cur.fetchall()
    conn.close()
    return data


app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return ""

if __name__ == "__main__":
    app.run(debug=True)



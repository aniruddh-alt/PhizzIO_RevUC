from werkzeug.utils import url_quote
from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from flask_session import Session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import psycopg2
import hashlib
### flask and auth lib
from flask import Flask, render_template, session, request, redirect, url_for, send_file, send_from_directory, make_response, flash
from flask_session import Session  # https://pythonhosted.org/Flask-Session
import msal
import io
import requests
import pandas as pd
import numpy as np
import os
### lib for this app
import json
from datetime import datetime, timedelta
import hashlib
import zipfile
import csv
import openpyxl
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import fonts,Font,PatternFill
import sqlite3
#import mysql.connector
import sendgrid
from sendgrid.helpers.mail import Mail, Cc
import base64


app = Flask(__name__)

# Configure the secret key for session management
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# Configure the database connection details
DATABASE_URL = 'postgresql://postgres:l1RFqY5YNx1ZqtUM@org-phizzio-inst-phizzio-standard.data-1.use1.tembo.io:5432/postgres'

# Initialize Flask-Session
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Database connection function
def connect_db():
    return psycopg2.connect(DATABASE_URL)

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Signup route
@app.route('/')
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        role = request.form.get('role')
        password = request.form.get('password')

        # Validate input
        if not username or not email or not password:
            flash('Please provide username, email, and password', 'error')
            return redirect(url_for('signup'))

        # Check if username or email already exists
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
                existing_user = cur.fetchone()
                if existing_user:
                    flash('Username or email already exists. Please choose different ones.', 'error')
                    return redirect(url_for('signup'))

                # Hash the password for security
                hashed_password = hashlib.sha256(password.encode()).hexdigest()
                cur.execute("INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)", (username, email, hashed_password,role))
                conn.commit()

        flash('Signup successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')
# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT user_id, password_hash FROM users WHERE username = %s", (username,))
                user = cur.fetchone()

                if user and user[1] == hashlib.sha256(password.encode()).hexdigest():
                    # Create a User object for Flask-Login
                    user_obj = User(user[0])
                    # Login the user
                    login_user(user_obj)
                    return redirect(url_for('home'))
                else:
                    flash('Invalid username or password', 'error')

    return render_template('login.html')

# Logout route
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logout successful'}), 200

# Example protected route
@app.route('/protected', methods=['GET'])
@login_required
def protected():
    return jsonify({'message': 'This is a protected route'}), 200

if __name__ == "__main__":
    app.run(debug=True)

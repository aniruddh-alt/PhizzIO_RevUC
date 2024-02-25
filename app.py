from werkzeug.utils import url_quote
from flask import Flask, request, jsonify, session, render_template, redirect, url_for, Response
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
from heel_slides import *
from datetime import timedelta


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
                cur.execute("SELECT user_id, password_hash, role FROM users WHERE username = %s", (username,))
                user = cur.fetchone()

                if user and user[1] == hashlib.sha256(password.encode()).hexdigest():
                    # Create a User object for Flask-Login
                    user_obj = User(user[0])
                    # Login the user
                    login_user(user_obj)
                    
                    if session.get('user') is None:
                        session['user'] = {}
                    session['user']['id'] = user[0]
                    session['user']['role'] = user[2]
                    session['user']['username'] = username
                        
                    if user[2] == 'Physiotherapist':
                        return redirect(url_for('physio'))
                    elif user[2] == 'Patient':
                        return redirect(url_for('patient_page'))
                else:
                    flash('Invalid username or password', 'error')

    return render_template('login.html')


@app.route('/physio')
@login_required
def physio():
    # Check if the current user is a physiotherapist
    if 'user' in session and session['user']['role'] == 'Physiotherapist':
        # Retrieve patients assigned to this physiotherapist
        patients = []
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM PATIENTS WHERE physio_id = %s", (str(session['user']['id']),))
                patients = cur.fetchall()

        return render_template('physio.html', assigned_patients=patients)
    else:
        # If the current user is not a physiotherapist, redirect to an appropriate page
        flash('You are not authorized to access this page', 'error')
        return redirect(url_for('login'))
    
from flask import render_template, request

@app.route('/phy/patient/<patient_id>', methods=['GET', 'POST'])
def patient_details(patient_id):
    if request.method == 'POST':
        # Retrieve form data
        with connect_db() as conn:
            with conn.cursor() as cur:
                exercise_name = request.form.get('exercise_name')
                reps = request.form.get('reps')
                sets = request.form.get('sets')
                notes = request.form.get('notes')
                thresh_angle = request.form.get('thresh_angle')
                cur.execute("INSERT INTO ASSIGN_EXERCISE (patient_id, physio_id, exercise_name, reps, sets, notes, assigned_date, threshold_angle) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_DATE, %s)", (patient_id, session['user']['id'], exercise_name, reps, sets, notes, int(thresh_angle)))
                conn.commit()  
    # Retrieve patient details
    patient = {}
    log = {}
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM PATIENTS WHERE patient_id = %s", (patient_id,))
            patient = cur.fetchone()
            cur.execute("SELECT * FROM PATIENT_EXERCISE_LOG WHERE patient_id = %s", (str(patient_id),))
            log = cur.fetchall()
            cur.execute("SELECT * FROM ASSIGN_EXERCISE WHERE patient_id = %s", (patient_id,))
            exercises_assigned = cur.fetchall()
    
    return render_template('patient_info.html', patient=patient, log=log, exercises_assigned=exercises_assigned)


@app.route('/patient', methods=['GET'])
def patient_page():
    # Retrieve patient information
    patient_info = {}

    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT patient_id FROM patients WHERE user_id = %s", (str(session['user']['id']),))
            patient_id = cur.fetchone()[0]
            cur.execute("SELECT * FROM patients WHERE patient_id = %s", (patient_id,))
            patient_info = cur.fetchone()

    # Retrieve information about the patient's physiotherapist
    physiotherapist_info = {}
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM physiotherapists WHERE physiotherapist_id = %s", (patient_info[7],))
            physiotherapist_info = cur.fetchone()

    # Retrieve assigned exercises for the patient
    assigned_exercises = []
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM assign_exercise WHERE patient_id = %s", (patient_id,))
            assigned_exercises = cur.fetchall()
            
    # exercise log:
    log = []
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM PATIENT_EXERCISE_LOG WHERE patient_id = %s", (str(patient_id),))
            log = cur.fetchall()

    return render_template('patient.html', patient=patient_info, physiotherapist=physiotherapist_info, exercises=assigned_exercises,log=log)

@app.route('/exercise/<exercise_name>/<patient_id>', methods=['POST', 'GET']) 
def exercise_guide(exercise_name, patient_id):
    if exercise_name == 'Heel Slides':
        return redirect('/heel_slides/{}'.format(patient_id))
    elif exercise_name == 'Knee Extensions':
        return redirect(f'/knee_extensions/{patient_id}')
    elif exercise_name == 'Squats':
        return redirect('/squats/{}'.format(patient_id))
    elif exercise_name == 'Arm Extensions':
        return redirect('/arm_extensions/{}'.format(patient_id))
    else:
        return redirect('/patient')

@app.route('/knee_extensions/<patient_id>', methods=['GET'])
def knee_extensions_route(patient_id):
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        return "Error: Unable to open the camera."

    completed, sets, reps, elapsed_time, mistakes = knee_extensions()
    update_exercise_log(patient_id, 'Knee Extensions', sets, reps, elapsed_time)
    cap.release()
    return redirect(url_for('patient_page'))

@app.route('/squats/<patient_id>', methods=['GET'])
def squat_route(patient_id):
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        return "Error: Unable to open the camera."

    completed, sets, reps, elapsed_time, mistakes = squats()
    print(completed, sets, reps, elapsed_time, mistakes)
    update_exercise_log(patient_id, 'Squats', sets, reps, elapsed_time)
    
    cap.release()

    return redirect(url_for('patient_page'))

def update_exercise_log(patient_id, exercise_name, sets, reps, elapsed_time):
    duration = str(timedelta(seconds=elapsed_time))
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO PATIENT_EXERCISE_LOG (patient_id, exercise_id, sets, reps, duration, date) VALUES (%s, %s, %s, %s, %s, CURRENT_DATE)", (patient_id, exercise_name, sets, reps, duration))
            conn.commit()

# Logout route
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    session.clear()  # Reset session
    return redirect(url_for('login')) 

# Example protected route
@app.route('/protected', methods=['GET'])
@login_required
def protected():
    return jsonify({'message': 'This is a protected route'}), 200

if __name__ == "__main__":
    app.run(debug=True)

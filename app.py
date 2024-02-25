from flask import Flask, request, jsonify, session
from flask_session import Session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import psycopg2
import hashlib

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
            cur.execute("SELECT id, password FROM users WHERE username = %s", (username,))
            user = cur.fetchone()

            if user and user[1] == hashlib.sha256(password.encode()).hexdigest():
                # Create a User object for Flask-Login
                user_obj = User(user[0])
                # Login the user
                login_user(user_obj)
                return jsonify({'message': 'Login successful'}), 200
            else:
                return jsonify({'error': 'Invalid username or password'}), 401

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

from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import json
import os
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Replace with a secure key

# File paths for persistent storage
USERS_FILE = 'users.json'
BOOKINGS_FILE = 'bookings.json'

# Load users from file or initialize with default
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            loaded_users = json.load(f)
            migrated_users = {}
            for username, value in loaded_users.items():
                if isinstance(value, str):  # Old format
                    migrated_users[username] = {'password': value, 'email': 'N/A', 'phone': 'N/A', 'dob': 'N/A'}
                else:  # New format
                    migrated_users[username] = value
            return migrated_users
    return {
        'visitor': {
            'password': 'museum2025',
            'email': 'visitor@example.com',
            'phone': '1234567890',
            'dob': '1990-01-01'
        }
    }

# Save users to file
def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

# Load bookings from file or initialize with empty list
def load_bookings():
    if os.path.exists(BOOKINGS_FILE):
        with open(BOOKINGS_FILE, 'r') as f:
            return json.load(f)
    return []

# Save bookings to file
def save_bookings(bookings):
    with open(BOOKINGS_FILE, 'w') as f:
        json.dump(bookings, f, indent=4)

# Initialize users and bookings
users = load_users()
bookings = load_bookings()

@app.route('/')
def index():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login_page'))
    # Pass email and phone as query parameters to index.html
    email = session.get('email', 'visitor@example.com')
    phone = session.get('phone', '1234567890')
    return redirect(url_for('index_page', email=email, phone=phone))

@app.route('/index')
def index_page():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login_page'))
    return render_template('index.html')

@app.route('/login', methods=['GET'])
def login_page():
    if 'logged_in' in session and session['logged_in']:
        return redirect(url_for('index'))
    return render_template('login.html', is_register=False, error=None)

@app.route('/register', methods=['GET'])
def register_page():
    if 'logged_in' in session and session['logged_in']:
        return redirect(url_for('index'))
    return render_template('login.html', is_register=True, error=None)

@app.route('/login', methods=['POST'])
def do_login():
    email = request.form.get('email')
    password = request.form.get('password')
    phone = request.form.get('phone')
    
    # Check if the email exists and the password matches
    user = next((u for u, data in users.items() if data['email'] == email), None)
    if user and users[user]['password'] == password:
        session['logged_in'] = True
        session['email'] = email
        session['phone'] = phone
        return redirect(url_for('index'))
    else:
        return render_template('login.html', is_register=False, error="Invalid email or password")

@app.route('/register', methods=['POST'])
def register():
    email = request.form.get('email')
    password = request.form.get('password')
    phone = request.form.get('phone')
    dob = request.form.get('dob-hidden')  # Hidden field with YYYY-MM-DD format

    # Check if email already exists
    if any(data['email'] == email for data in users.values()):
        return render_template('login.html', is_register=True, error="Email already exists")

    # Validate inputs (already validated client-side, but good to double-check)
    if not email or not password or not phone or not dob:
        return render_template('login.html', is_register=True, error="All fields are required")
    if len(password) < 8:
        return render_template('login.html', is_register=True, error="Password must be at least 8 characters long")
    if not phone.isdigit() or len(phone) != 10:
        return render_template('login.html', is_register=True, error="Phone number must be a 10-digit number")

    # Create a new user (using email as the key for simplicity)
    users[email] = {'password': password, 'email': email, 'phone': phone, 'dob': dob}
    save_users(users)
    return render_template('login.html', is_register=False, error="Registration successful! Please log in.")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/book', methods=['POST'])
def book():
    data = request.get_json()
    booking = {
        'booking_id': str(uuid.uuid4()),
        'phone': data['phone'],
        'email': data['email'],
        'museum': data['museum'],
        'service': data['service'],
        'timeSlot': data['timeSlot'],
        'numTickets': data['numTickets'],
        'date': data.get('date', '2025-03-21')  # Default to current date if not provided
    }
    bookings.append(booking)
    save_bookings(bookings)
    return jsonify({'booking_id': booking['booking_id']})

if __name__ == '__main__':
    app.run(debug=True)
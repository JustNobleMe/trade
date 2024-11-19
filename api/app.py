from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
import psycopg2
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key

# Database Configuration
DB_CONFIG = {
    'host': 'ep-tiny-art-a4b10csj.us-east-1.aws.neon.tech',
    'database': 'trade',
    'user': 'neondb_owner',
    'password': 'd0PjqpYGoUK4',
    'port': '5432',
    'sslmode': 'require'
}

# Helper function to connect to the database
def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"Database connection failed: {e}")
        return None

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        plan = request.form['plan']

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            # Check if the email already exists
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            existing_user = cursor.fetchone()
            if existing_user:
                flash("Email already registered. Please log in.")
                return redirect(url_for('login'))

            # Insert the new user
            cursor.execute(
                "INSERT INTO users (name, email, password, plan) VALUES (%s, %s, %s, %s)",
                (name, email, password, plan)
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash("Registration successful! Please log in.")
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            # Authenticate the user
            cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
            user = cursor.fetchone()
            if user:
                session['user_id'] = user[0]
                session['name'] = user[1]
                session['plan'] = user[4]
                cursor.close()
                conn.close()
                flash("Login successful!")
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid credentials. Please try again.")
                cursor.close()
                conn.close()
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        flash("Please log in to access the dashboard.")
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        target_plans = request.form.getlist('target_plans')  # Get selected target plans from the form

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            # Insert the content into the database
            cursor.execute(
                "INSERT INTO content (title, body, target_plans) VALUES (%s, %s, %s)",
                (title, body, json.dumps(target_plans))  # Store target plans as a JSON array
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash("Content posted successfully!")

    return render_template('dashboard.html', username=session['name'], plan=session['plan'])

@app.route('/admin', methods=['GET'])
def admin_dashboard():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        # Retrieve all posted content
        cursor.execute("SELECT * FROM content")
        contents = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('admin_dashboard.html', contents=contents)
    flash("Failed to fetch content. Please try again later.")
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for('home'))

# Error Handler
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_message='Page not found!'), 404

if __name__ == '__main__':
    app.run(debug=True)

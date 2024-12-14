from flask import Flask, render_template, request, redirect, url_for, flash
from app.auth import register_user, login_user
from app.models import Login
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
app = Flask(__name__)
#app = Flask(__name__, template_folder='template')
#app.secret_key = "your_secret_key"  # Required for flash messages
#app.secret_key = os.getenv("SECRET_KEY")
# Load environment variables (for DB connection details)
load_dotenv()
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")  # Example: postgresql://user:password@localhost/dbname
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv("SECRET_KEY")

# Initialize the database
db = SQLAlchemy(app)

# Home Route (After successful login)
@app.route('/')
def home():
    return render_template('home.html')

# Registration Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        #confirm_password = request.form['confirm_password']
        email = request.form['email']
        
        '''
        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect(url_for('register'))
        '''
        if register_user(username, password, email):  # Attempt to register user
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
        else:
            flash("Registration failed. Username or email may already exist.", "error")
            return redirect(url_for('register'))
    return render_template('register.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if login_user(username, password):  # Check login credentials
            flash("Login successful!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid username or password. Please try again.", "error")
            return redirect(url_for('login'))
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)

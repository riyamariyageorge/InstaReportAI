from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.auth import register_user, login_user
from app.models import Login

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/')
def home():
    return render_template('home.html')

@auth_bp.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        existing_user = Login.query.filter((Login.username == username) | (Login.email == email)).first()
        if existing_user:
            flash("Registration failed. Username or email already exists.", "error")
            return render_template('register.html', username=username, email=email)

        # Register the user if no existing user found
        result = register_user(username, password, email)

        if result:  # If the registration was successful
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('auth_bp.login'))
        else:  # If registration failed
            flash("Registration failed. Please try again.", "error")
            return redirect(url_for('auth_bp.register'))

    return render_template('register.html')

# Login Route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if login_user(username, password):  # Check login credentials
            flash("Login successful!", "success")
            return redirect(url_for('auth_bp.home'))  # Redirect to the home route
        else:
            flash("Invalid username or password. Please try again.", "error")
            return redirect(url_for('auth_bp.login'))

    return render_template('login.html')
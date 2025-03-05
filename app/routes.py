from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.auth import register_user, login_user
from app.models import Login, db
from authlib.integrations.flask_client import OAuthError
from app import oauth

import secrets
from dotenv import load_dotenv
#from extracttext import process_event_poster
auth_bp = Blueprint('auth_bp', __name__, template_folder='templates')

load_dotenv()


# Create the OAuth object for Google login

@auth_bp.route('/')
def home():
    username = session.get('user')
    if username:
        return redirect(url_for('auth_bp.dashboard'))
    return render_template('home.html')

@auth_bp.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        username = request.form.get('username') 

        existing_user = Login.query.filter((Login.email == email) | (Login.username == username)).first()
        if existing_user:
            flash("Registration failed. Username or email already exists.", "error")
            return render_template('register.html', email=email)
        if not username:
            flash("Username is required for traditional registration.", "error")
            return render_template('register.html', email=email)
        # Register the user if no existing user found
        
        result, error_message = register_user( username, password, email)

        if result:  # If the registration was successful
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('auth_bp.login'))
        else:  # If registration failed
            flash(f"Registration failed: {error_message}", "error")
            return redirect(url_for('auth_bp.register'))
            

    return render_template('register.html')

# Login Route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if login_user(username, password):  # Check login credentials
            session['user'] = username
            flash("Login successful!", "success")
            session['_flashes'] = [] 
            return redirect(url_for('auth_bp.dashboard'))  # Redirect to the dashboard route
        else:
            flash("Invalid username or password. Please try again.", "error")
            return redirect(url_for('auth_bp.login'))

    return render_template('login.html')

@auth_bp.route('/logout', methods=['GET','POST'])
def logout():
    session.clear()
    flash("You have been logged out.","success")
    return redirect(url_for('auth_bp.login'))

@auth_bp.route('/google-login')
def google_login():
    nonce = secrets.token_urlsafe(16)
    session['oauth_nonce'] = nonce
    redirect_uri = url_for('auth_bp.google_login_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri, nonce=nonce)

# Google Authorized Callback Route
@auth_bp.route('/auth/google/callback')
def google_login_callback():
    try:
        token = oauth.google.authorize_access_token()
        nonce = session.get('oauth_nonce')
        user_info = oauth.google.parse_id_token(token, nonce=nonce)
        email = user_info['email']
        username = email.split('@')[0]  # Use email prefix as the username if needed
        
        # Check if the user already exists
        existing_user = Login.query.filter_by(email=email).first()
        if existing_user:
            session['user'] = existing_user.username
            #flash(f"Welcome back, {existing_user.username}!", "success")
        else:
            # Register the new Google user
            new_user = Login(email=email, password=None, username=username, is_google_user=True)
            db.session.add(new_user)
            db.session.commit()
            session['user'] = username 
            flash(f"Welcome, {username}!", "success")

        
        #flash(f"Welcome, {username}!", "success") 
        return redirect(url_for('auth_bp.dashboard'))

    except OAuthError as e:
        flash("Error during Google login. Please try again.", "error")
        return redirect(url_for('auth_bp.login'))

@auth_bp.route('/dashboard')
def dashboard():
    username = session.get('user')
    if not username:
        flash("Please log in to access the dashboard.","warning")
        return redirect(url_for('auth_bp.login'))
    return render_template('dashboard.html', username=username)



@auth_bp.route('/userguide')
def userguide():
    username = session.get('user')
    if not username:
        flash("Please log in to access the userguide page.", "warning")
        return redirect(url_for('auth_bp.login'))
    return render_template('userguide.html', username=username)


@auth_bp.route('/imagegallary')
def imagegallary():
    username = session.get('user')
    if not username:
        flash("Please log in to access the gallary page.", "warning")
        return redirect(url_for('auth_bp.login'))
    return render_template('imagegallary.html', username=username)

    
    
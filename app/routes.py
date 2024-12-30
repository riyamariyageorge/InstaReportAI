from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.auth import register_user, login_user
from app.models import Login
#from extracttext import process_event_poster
auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/')
def home():
    username = session.get('user')
    if username:
        return redirect(url_for('auth_bp.dashboard'))
    return render_template('home.html')

@auth_bp.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')

        existing_user = Login.query.filter((Login.username == username) | (Login.email == email)).first()
        if existing_user:
            flash("Registration failed. Username or email already exists.", "error")
            return render_template('register.html', username=username, email=email)

        # Register the user if no existing user found
        result, error_message = register_user(username, password, email)

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
            return redirect(url_for('auth_bp.dashboard', username=username))  # Redirect to the dashboard route
        else:
            flash("Invalid username or password. Please try again.", "error")
            return redirect(url_for('auth_bp.login'))

    return render_template('login.html')
@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.","success")
    return redirect(url_for('auth_bp.login'))


@auth_bp.route('/dashboard')
def dashboard():
    username = session.get('user')
    if not username:
        flash("Please log in to access the dashboard.","warning")
        return redirect(url_for('auth_bp.login'))
    return render_template('dashboard.html', username=username)



@auth_bp.route('/templates')
def templates():
    username = session.get('user')
    if not username:
        flash("Please log in to access the templates page.", "warning")
        return redirect(url_for('auth_bp.login'))

    # Define the list of templates
   # templates = [
    #    {"file": "templates3.docx", "image": "placeholder-image.jpg", "name": "Workshop Report"}
       # {"file": "templates4.docx", "image": "template2.jpg", "name": "Project Report"},
       # {"file": "templates5.docx", "image": "template3.jpg", "name": "Business Strategy Outline"}
    #]
    return render_template('tem.html', username=username)


    
    
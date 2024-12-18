from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import os
from app.extracttext import process_event_poster
from app.models import Event, db
from datetime import datetime
# Blueprint configuration
upload_bp = Blueprint('upload_bp', __name__, template_folder='templates', static_folder='static')

# Path to save uploaded files
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the folder exists

# Helper function to check file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route: Upload Event Poster
@upload_bp.route('/upload2', methods=['GET', 'POST'])
def upload_poster():
    username = session.get('user')
    if not username:
        flash("Please log in to upload posters.", "warning")
        return redirect(url_for('auth_bp.login'))
    event_data = session.get('extracted_data', {})

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)

            # Process the file using OCR
            extracted_data = process_event_poster(file_path)
            print("Extracted Data:", extracted_data)

            # Store the extracted data in session
            if extracted_data:
                session['extracted_data'] = extracted_data
                print("Stored in session:",session['extracted_data'])
                session['poster_path'] = file_path
                flash("Extraction successful! Please review the details below.", "success")
                return redirect(url_for('upload_bp.edit_event_details'))
            else:
                flash("Failed to extract data from the poster.", "error")
                return redirect(request.url)
            
     
    return render_template('upload2.html', username=username, event_data=event_data)

# Route: Edit Event Details
@upload_bp.route('/edit_event_details', methods=['GET', 'POST'])
def edit_event_details():
    username = session.get('user')
    if not username:
        flash("Please log in to edit event details.", "warning")
        return redirect(url_for('auth_bp.login'))

    event_data = session.get('extracted_data', {})
    poster_path = session.get('poster_path','')

    if request.method == 'POST':
        title = request.form.get('eventTitle')
        date = request.form.get('eventDate')
        time = request.form.get('eventTime')
        venue = request.form.get('eventVenue')
        if not (title and date and time and venue):
            flash("All fields are required.", "error")
            return redirect(request.url)
        

        try:
            event = Event(
                title=title,
                date=datetime.strptime(date, '%Y-%m-%d').date(),
                time=datetime.strptime(time, '%H:%M').time(),
                venue=venue,
                poster_path=poster_path
            )
            db.session.add(event)
            db.session.commit()

            # Clear session data
            session.pop('extracted_data', None)
            session.pop('poster_path', None)

            flash("Event saved successfully!", "success")
            return redirect(url_for('auth_bp.dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {e}", "error")
            return redirect(request.url)

    return render_template('upload2.html', username=username, event_data=event_data)

    

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import os
from app.extracttext import process_event_poster
from app.models import Event, db
from datetime import datetime
from dateutil.parser import parse as parse_date
import re
# Blueprint configuration
upload_bp = Blueprint('upload_bp', __name__, template_folder='../templates', static_folder='../static')

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
        if request.is_json:
            return {"success": False, "message": "Please log in to upload posters"}, 401
        flash("Please log in to upload posters.", "warning")
        return redirect(url_for('auth_bp.login'))
   # event_data = session.get('extracted_data', {})

    if request.method == 'POST':
        if 'file' not in request.files:
            #flash('No file uploaded', 'error')
            #return redirect(request.url)
            return {"success": False, "message": "No file selected."}, 400

        file = request.files['file']
        if file.filename == '':
            #flash('No file selected', 'error')
            #return redirect(request.url)
            return {"success": False, "message": "No file selected."}, 400


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
                #print("Stored in session:",session['extracted_data'])
                session['poster_path'] = file_path
                #flash("Extraction successful! Please review the details below.", "success")
                #return redirect(url_for('upload_bp.edit_event_details'))
                return {"success": True, "extracted_data": extracted_data}, 200
            else:
                #flash("Failed to extract data from the poster.", "error")
                #return redirect(request.url)
                return {"success": False, "message": "Failed to extract data from the poster."}, 500
    session['_flashes']=[]        
    event_data = session.get('extracted_data',{})
    return render_template('upload2.html', username=username, event_data=event_data)

# Route: Edit Event Details
@upload_bp.route('/edit_event_details', methods=['GET', 'POST'])
def edit_event_details():
    username = session.get('user')
    if not username:
        flash("Please log in to edit event details.", "warning")
        return redirect(url_for('auth_bp.login'))

    # Fetch existing session data
    event_data = session.get('extracted_data', {})
    poster_path = session.get('poster_path', '')

    if request.method == 'POST':
        print("POST request received at /edit_event_details")
        # Capture edited details from the form
        title = request.form.get('eventTitle')
        raw_date = request.form.get('eventDate')
        raw_time = request.form.get('eventTime')
        venue = request.form.get('eventVenue')

        # Validate inputs
        if not (title and raw_date and raw_time and venue):
            flash("All fields are required.", "error")
            return redirect(request.url)

        try:

            session['extracted_data'] = {
                'title': title,
                'date': raw_date,
                'time': raw_time,
                'venue': venue
            }
            
            # Parse date and time inputs
            event_date = parse_date(raw_date, dayfirst=True).date()
            start_time, end_time = None, None

            if "to" in raw_time:
                start_time, end_time = [
                    datetime.strptime(t.strip(), '%I:%M %p').time()
                    for t in raw_time.split("to")
                ]
            else:
                start_time = datetime.strptime(raw_time.strip(), '%I:%M %p').time()

            # Save the event details to the database
            
            event = Event(
                title=title,
                date=event_date,
                start_time=start_time,
                end_time=end_time,
                venue=venue,
                poster_path=poster_path
            )
            db.session.add(event)
            db.session.commit()
            print("Event saved to the database successfully.")

            # Clear session data
           # session.pop('extracted_data', None)
            session.pop('poster_path', None)
            
            

            #print("Session updated with edited details:", session['extracted_data'])
            #session.modified = True 

            flash("Event saved successfully!", "success")
            return redirect(url_for('upload_bp.edit_event_details'))

        except ValueError as ve:
            flash(str(ve), "error")
            return redirect(request.url)

        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {e}", "error")
            return redirect(request.url)
    #print("GET request received at /edit_event_details")
    return render_template('upload2.html', username=username, event_data=event_data)


@upload_bp.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')
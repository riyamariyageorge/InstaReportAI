from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
import os
from app.extracttext import extract_event_details
from app.models import Event, db
from datetime import datetime
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

# Helper function to parse date in various formats
def parse_date(date_str, dayfirst=False):
    # Modify the format based on the 'dayfirst' flag
    if dayfirst:
        # For day-first, we expect formats like "27 July 2024"
        formats = ("%d %B %Y", "%d %b %Y", "%d-%m-%Y")
    else:
        # For month-first, we expect formats like "July 27 2024" or "2024-07-27"
        formats = ("%d %B %Y", "%d %b %Y", "%Y-%m-%d")

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unknown date format: {date_str}")


# Helper function to parse time ranges or single times
def parse_time_range(time_str):
    """Parse time ranges like '8pm-9pm', '8:00pm-9:00pm', '8.00pm-9.00pm', or single times."""
    # Regex for time range with variations in formatting
    time_range = re.match(
        r"(\d{1,2}([:.]\d{2})?\s*(am|pm)?)[\s\-to]*(\d{1,2}([:.]\d{2})?\s*(am|pm)?)", 
        time_str, re.IGNORECASE
    )
    
    if time_range:
        start, end = time_range.group(1), time_range.group(4)
        
        # Normalize and parse times
        start_time = datetime.strptime(start.replace('.', ':'), "%I:%M %p") if ':' in start else datetime.strptime(start.replace('.', ''), "%I%p")
        end_time = datetime.strptime(end.replace('.', ':'), "%I:%M %p") if ':' in end else datetime.strptime(end.replace('.', ''), "%I%p")
        
        return start_time.time(), end_time.time()  # Return only time parts

    # Regex for single time
    single_time = re.match(r"(\d{1,2}([:.]\d{2})?\s*(am|pm)?)", time_str, re.IGNORECASE)
    if single_time:
        start_time = datetime.strptime(single_time.group(1).replace('.', ':'), "%I:%M %p") if ':' in single_time.group(1) else datetime.strptime(single_time.group(1).replace('.', ''), "%I%p")
        return start_time.time(), None

    raise ValueError(f"Unknown time format: {time_str}")


# Route: Upload Event Poster
@upload_bp.route('/upload2', methods=['GET', 'POST'])
def upload_poster():
    username = session.get('user')
    if not username:
        if request.is_json:
            return {"success": False, "message": "Please log in to upload posters"}, 401
        flash("Please log in to upload posters.", "warning")
        return redirect(url_for('auth_bp.login'))

    if request.method == 'POST':
        if 'file' not in request.files:
            return {"success": False, "message": "No file selected."}, 400

        file = request.files['file']
        if file.filename == '':
            return {"success": False, "message": "No file selected."}, 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)

            # Extract event details
            extracted_data = extract_event_details(file_path)

            if extracted_data:
                session['extracted_data'] = {
                    'event_name': extracted_data.get('event_name'),
                    'date': extracted_data.get('date'),
                    'time': extracted_data.get('time'),
                    'venue': extracted_data.get('venue'),
                }
                session['poster_path'] = file_path
                return {"success": True, "extracted_data": session['extracted_data']}, 200
            else:
                return {"success": False, "message": "Failed to extract data from the poster."}, 500

    event_data = session.get('extracted_data', {})
    return render_template('upload2.html', username=username, event_data=event_data)

# Route: Edit Event Details
@upload_bp.route('/edit_event_details', methods=['GET', 'POST'])
def edit_event_details():
    username = session.get('user')
    if not username:
        flash("Please log in to edit event details.", "warning")
        return redirect(url_for('auth_bp.login'))

    event_data = session.get('extracted_data', {})
    poster_path = session.get('poster_path', '')

    if request.method == 'POST':
    # Capture edited details from the form
        title = request.form.get('eventTitle')
        raw_date = request.form.get('eventDate')
        raw_time = request.form.get('eventTime')
        venue = request.form.get('eventVenue')

        if not (title and raw_date and raw_time and venue):
            flash("All fields are required.", "error")
            return redirect(request.url)

        try:
            session['extracted_data'] = {
                'event_name': title,
                'date': raw_date,
                'time': raw_time,
                'venue': venue,
            }
            event_date = parse_date(raw_date, dayfirst=True)

            # Parse time range if provided
            start_time, end_time = None, None
            if "to" in raw_time:
                start_time, end_time = parse_time_range(raw_time) 
            else:
                start_time, _ = parse_time_range(raw_time)

            # Save event details to the database
            event = Event(
                title=title,
                date=event_date,
                start_time=start_time,
                end_time=end_time,
                venue=venue,
                poster_path=session.get('poster_path', '')
            )
            db.session.add(event)
            db.session.commit()

            session.pop('extracted_data', None)
            flash("Event saved successfully!", "success")
            return redirect(url_for('upload_bp.edit_event_details'))

        except ValueError as ve:
            flash(str(ve), "error")
            return redirect(request.url)
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {e}", "error")
            return redirect(request.url)


    return render_template('upload2.html', username=username, event_data=event_data)

# Route: Get Extracted Data (API)
@upload_bp.route('/get_extracted_data', methods=['GET'])
def get_extracted_data():
    if 'extracted_data' in session:
        return jsonify({'success': True, 'data': session['extracted_data']})
    return jsonify({'success': False, 'error': 'No data found in session'}), 404

# Route: Chatbot Page
@upload_bp.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

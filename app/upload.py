from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
import os
from app.extracttext import extract_event_details
from app.models import Event, db
from datetime import datetime
import re
import pandas as pd
from flask import send_file
from app.pdf_generator import generate_event_report
from app.groq_api import generate_event_description
#from app.constants import CONFERENCE_COLUMNS, WORKSHOP_COLUMNS, SEMINAR_COLUMNS
# Blueprint configuration
upload_bp = Blueprint('upload_bp', __name__, template_folder='../templates', static_folder='../static')

# Path to save uploaded files
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the folder exists

# Helper function to check file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


'''
def allowed_excel_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXCEL_EXTENSIONS
'''
# Helper function to parse date in various formats
def parse_date(date_str, dayfirst=False):
    date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
    formats = [
        "%B %d, %Y",  # Example: "May 15, 2024"
        "%d %B %Y",   # Example: "15 May 2024"
        "%Y-%m-%d",   # Example: "2024-05-15"
        "%m/%d/%Y",   # Example: "05/15/2024"
        "%d-%m-%Y",   # Example: "15-05-2024"
        "%d %b %Y",   # Example: "15 May 24"
        "%B %d %Y",   # Example: "May 15 2024"
    ]
     
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unknown date format: {date_str}")


# Helper function to parse time ranges or single times
def parse_time_range(time_str):
    """Parse time ranges like '1.30pm-3.30pm', '8pm-9pm', or single times."""
    # Clean up the input string: remove extra spaces and ensure consistent format
    time_str = time_str.strip().lower().replace(" ", "").replace(".",":")

    # Regex for time range with variations in formatting
    time_range = re.match(
        r"(\d{1,2}([:.]\d{2})?(am|pm)?)[\s\-to]*(\d{1,2}([:.]\d{2})?(am|pm)?)", 
        time_str, re.IGNORECASE
    )

    if time_range:
        start, end = time_range.group(1), time_range.group(4)

        # Normalize times (replace '.' with ':' if needed)
        #start = start.replace(".", ":")
        #end = end.replace(".", ":")

        # If no minutes are provided, assume 00 minutes
        if len(start.split(":")) == 1:
            start = start + ":00"
        if len(end.split(":")) == 1:
            end = end + ":00"

        # Parse start and end times
        try:
            start_time = datetime.strptime(start, "%I:%M%p")  # With minutes
        except ValueError:
            # Handle invalid time string if it occurs
            raise ValueError(f"Invalid start time format: {start}")

        try:
            end_time = datetime.strptime(end, "%I:%M%p")  # With minutes
        except ValueError:
            # Handle invalid time string if it occurs
            raise ValueError(f"Invalid end time format: {end}")

        return start_time.time(), end_time.time()

    # Regex for single time (with or without minutes)
    single_time = re.match(r"(\d{1,2}([:.]\d{2})?(am|pm)?)", time_str, re.IGNORECASE)
    if single_time:
        start = single_time.group(1).replace(".", ":")

        # If no AM/PM is provided, default to AM
        if not re.search(r"(am|pm)", start):
            start += "am"
        # If no minutes are provided, assume 00 minutes
        if len(start.split(":")) == 1:
            start = start + ":00"

        try:
            start_time = datetime.strptime(start, "%I:%M%p")  # With minutes
        except ValueError:
            # Handle invalid time string if it occurs
            raise ValueError(f"Invalid start time format: {start}")

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
                    'description':''
                }
                session['poster_path'] = file_path
                return {"success": True, "extracted_data": session['extracted_data']}, 200
            else:
                flash("Failed to extract data. Please edit details manually.", "error")
                session['extracted_data'] = {
                    'event_name': '',
                    'date': '',
                    'time': '',
                    'venue': '',
                    'description': ''
                }
            return redirect(url_for('upload_bp.edit_event_details'))
        
    event_data = session.get('extracted_data', {
        'event_name': '',
        'date': '',
        'time': '',
        'venue': '',
        'description': ''
    })    
    return render_template('upload2.html', username=username, event_data=event_data)

# Route: Edit Event Details
@upload_bp.route('/edit_event_details', methods=['GET', 'POST'])
def edit_event_details():
    username = session.get('user')
    if not username:
        flash("Please log in to edit event details.", "warning")
        return redirect(url_for('auth_bp.login'))

    # Get the extracted data or initialize an empty dictionary
    event_data = session.get('extracted_data', {
        'event_name': '',
        'date': '',
        'time': '',
        'venue': '',
        'description': ''
    })
    poster_path = session.get('poster_path', '')

    if request.method == 'POST':
        # Capture edited details from the form
        title = request.form.get('eventTitle')
        raw_date = request.form.get('eventDate')
        raw_time = request.form.get('eventTime')
        venue = request.form.get('eventVenue')

        # Check if all required fields are present
        if not (title and raw_date and raw_time and venue):
            flash("All fields are required.", "error")
            return redirect(request.url)

        try:
            # Update session data with the form inputs
            event_data = {
                'event_name': title,
                'date': raw_date,
                'time': raw_time,
                'venue': venue,
            }
            session['extracted_data'] = event_data

            # Parse and validate date
            event_date = parse_date(raw_date, dayfirst=True)

            # Parse time range
            start_time, end_time = parse_time_range(raw_time)

            # Generate event description using Groq API
            #input_text = f"Generate a short description for an event titled '{title}', happening on {raw_date} at {raw_time}, at the venue '{venue}'."
            event_description = generate_event_description(event_data)

            # Save event details to the database
            event = Event(
                title=title,
                date=event_date,
                start_time=start_time,
                end_time=end_time,
                venue=venue,
                poster_path=poster_path,
                description=event_description
            )
            db.session.add(event)
            db.session.commit()
            event_data['description'] = event_description
            
            output_pdf_path = os.path.join("static", "event_report.pdf")
            generate_event_report(event_data, output_pdf_path)
            
            flash("Event saved successfully!", "success")
            return redirect(url_for('upload_bp.edit_event_details'))

        except ValueError as ve:
            flash(str(ve), "error")
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {e}", "error")

    # Render the page with updated session data
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



@upload_bp.route('/view_pdf', methods=['GET'])
def view_pdf():
    # Ensure the PDF file is generated and available
    output_pdf_path = os.path.join("static", "event_report.pdf")
    if not os.path.exists(output_pdf_path):
        flash("The PDF file is not available.", "error")
        return redirect(url_for('upload_bp.edit_event_details'))
    
    # Serve the PDF file
    return send_file(output_pdf_path, as_attachment=False)


'''
@upload_bp.route('/download_report', methods=['GET'])
def download_report():
    event_data = session.get('extracted_data', {})
    if not event_data:
        flash("No event details available for report generation.", "error")
        return redirect(url_for('upload_bp.edit_event_details'))

    try:
        # Generate PDF report
        pdf_path = os.path.join('static', 'reports', f"event_report.pdf")
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
        generate_event_report(event_data, pdf_path)

        # Serve the PDF as a downloadable file
        return send_file(pdf_path, as_attachment=True)

    except Exception as e:
        flash(f"An error occurred while generating the report: {e}", "error")
        return redirect(url_for('upload_bp.edit_event_details'))
    
'''
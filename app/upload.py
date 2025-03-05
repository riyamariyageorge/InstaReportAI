from flask import Flask, Blueprint, request, jsonify, render_template, session, send_file
import os
import base64
import google.generativeai as genai
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import re
import json
import time
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import simpleSplit
from io import BytesIO
# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for session storage
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
TEMPLATE_PATH = "templates/Header.pdf"
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
upload_bp = Blueprint('upload_bp', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def encode_file(file_path):
    """Convert files to Base64"""
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def format_extracted_text(text):
    """
    Convert extracted text into well-structured HTML:
    - Converts Markdown `**bold**` to `<b>bold</b>`
    - Converts `* Bullet points` to `<ul><li>Bullet points</li></ul>`
    """
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)  # Convert **Bold** to <b>Bold</b>
    text = re.sub(r'\n\s*\*\s(.*?)', r'<li>\1</li>', text)  # Convert * List items to <li>
    text = re.sub(r'(?:<li>.*?</li>)+', lambda m: f"<ul>{m.group()}</ul>", text, flags=re.DOTALL)  # Wrap <li> items in <ul>
    return text.replace("\n", "<br>")  # Preserve new lines

@upload_bp.route('/upload', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'GET':
        return render_template('upload2.html')

    if 'files' not in request.files:
        return jsonify({"error": "No files provided"}), 400

    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({"error": "No files selected"}), 400

    extracted_details = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            try:
                file_data = encode_file(filepath)
                mime_type = 'application/pdf' if filename.endswith('.pdf') else 'image/jpeg'

                summary_prompt = """
                Extract and structure event-related details into a well-formatted output:
                - <b>Event Title:</b> (Title in bold)
                - <b>Date & Time:</b> (Event schedule)
                - <b>Venue:</b> (Location details)
                - <b>Organizers:</b> (List organizers and collaborators)
                - <b>Speakers:</b> (Names & credentials)
                - <b>Program Flow:</b> (Breakdown of key activities)
                - <b>Participants:</b> (Who can attend)
                - <b>Key Outcomes:</b> (Expected results)
                - <b>Additional Info:</b> (Any other relevant details)
                
                Use:
                - Bullet points `<ul><li>item</li></ul>` for lists.
                - `<br>` for line breaks.
                """

                response = model.generate_content([
                    {'mime_type': mime_type, 'data': file_data},
                    summary_prompt
                ])

                structured_response = format_extracted_text(response.text if response.text else "No details extracted.")
                extracted_details.append(f"<h3>📌 Event Details from {filename}:</h3><br>{structured_response}")

            except Exception as e:
                extracted_details.append(f"<h3>❌ Error processing {filename}:</h3> {str(e)}")

            os.remove(filepath)

    summary = "<br><hr><br>".join(extracted_details)
    session['extracted_text'] = summary
    # Reset chat state when new files are uploaded
    if 'chat_state' in session:
        session.pop('chat_state')
    if 'collected_details' in session:
        session.pop('collected_details')

    return jsonify({"summary": summary})

@upload_bp.route('/chatbot', methods=['POST'])
def chatbot():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    extracted_text = session.get('extracted_text', '')
    
    # Initialize chat state if not already done
    if 'chat_state' not in session:
        session['chat_state'] = {
            'stage': 'init',
            'current_question_index': 0,
            'missing_details': [],
            'collected_details': {},
            'open_ended_question_asked': False,
            'additional_info': ''
        }
        # Store as JSON string to avoid session serialization issues
        session['chat_state'] = json.dumps(session['chat_state'])
    
    # Parse the chat state from the session
    chat_state = json.loads(session['chat_state'])
    
    # If we're just starting, analyze the extracted text for missing details
    if chat_state['stage'] == 'init':
        analysis_prompt = f"""
        You are an AI assistant refining event details for a report.

        ### **Task**
        1. Analyze the extracted event details provided below.
        2. Identify important missing or incomplete information necessary for a complete event report.
        3. For each missing detail, provide a specific question to ask the user.
        4. **Exclude any details that are already mentioned** in the extracted event text.
        5. Focus on the most important missing details, limit to 6 max.

        ### **Extracted Event Details**
        {extracted_text}

        ### **Response Format**
        Return a JSON array of objects, each with:
        - "detail_name": short name of the missing detail (e.g., "Registration_Process")
        - "question": specific question to ask about this detail (e.g., "How can participants register for this event?")

        Example:
        [
            {{"detail_name": "Registration_Process", "question": "How can participants register for this event?"}},
            {{"detail_name": "Target_Audience", "question": "Who is the target audience for this event?"}}
        ]
        """

        response = model.generate_content(analysis_prompt)
        try:
            # Try to parse the response as JSON
            missing_details = json.loads(response.text)
            # Validate structure
            if not isinstance(missing_details, list):
                # Fallback if not a list
                missing_details = []
        except:
            # If parsing fails, try to extract JSON from text
            match = re.search(r'\[\s*{.*}\s*\]', response.text, re.DOTALL)
            if match:
                try:
                    missing_details = json.loads(match.group(0))
                except:
                    missing_details = []
            else:
                missing_details = []
        
        # Update chat state
        chat_state['missing_details'] = missing_details
        chat_state['stage'] = 'confirm_collection'
        session['chat_state'] = json.dumps(chat_state)
        
        # Ask if user wants to add details
        if missing_details:
            detail_names = [detail['detail_name'].replace('_', ' ') for detail in missing_details]
            return jsonify({
                "response": f"I've analyzed the event information and found we could add a few more details to make the report more complete. Would you like to add information about: {', '.join(detail_names)}? (Yes/No)"
            })
        else:
            chat_state['stage'] = 'open_ended_question'
            session['chat_state'] = json.dumps(chat_state)
            return jsonify({
                "response": "The event details look comprehensive! Is there any further information you'd like to add to the report?"
            })
    
    # Handle user response to the confirmation question
    elif chat_state['stage'] == 'confirm_collection':
        if 'yes' in user_message.lower() or 'sure' in user_message.lower() or 'ok' in user_message.lower():
            if chat_state['missing_details']:
                chat_state['stage'] = 'collecting'
                first_question = chat_state['missing_details'][0]['question']
                session['chat_state'] = json.dumps(chat_state)
                return jsonify({"response": first_question})
            else:
                chat_state['stage'] = 'open_ended_question'
                session['chat_state'] = json.dumps(chat_state)
                return jsonify({
                    "response": "Is there any further information you'd like to add to the report?"
                })
        else:
            chat_state['stage'] = 'open_ended_question'
            session['chat_state'] = json.dumps(chat_state)
            return jsonify({
                "response": "No problem! Is there any further information you'd like to add to the report?"
            })
    
    # Collection stage - store answers and ask next question
    elif chat_state['stage'] == 'collecting':
        # Store the answer to the current question
        current_index = chat_state['current_question_index']
        detail_name = chat_state['missing_details'][current_index]['detail_name']
        chat_state['collected_details'][detail_name] = user_message
        
        # Move to the next question or finish
        current_index += 1
        chat_state['current_question_index'] = current_index
        
        # Check if we have more questions
        if current_index < len(chat_state['missing_details']):
            next_question = chat_state['missing_details'][current_index]['question']
            session['chat_state'] = json.dumps(chat_state)
            return jsonify({"response": next_question})
        else:
            # We've collected all specified missing details
            # Now ask the open-ended question
            chat_state['stage'] = 'open_ended_question'
            session['chat_state'] = json.dumps(chat_state)
            return jsonify({
                "response": "Thank you for providing those details! Is there any further information you'd like to add that I didn't specifically ask about?"
            })
    
    # Open-ended question stage - allow user to add anything else they want
    elif chat_state['stage'] == 'open_ended_question':
        if 'no' in user_message.lower() or 'that is all' in user_message.lower() or 'nothing else' in user_message.lower():
            # Update the extracted text with the collected details
            additional_details = ""
            if chat_state.get('collected_details'):
                additional_details += "<br><b>Additional Details:</b><br>" + "<br>".join(
                    [f"<b>{key.replace('_', ' ').title()}:</b> {value}" for key, value in chat_state['collected_details'].items()]
                )
            
            session['extracted_text'] = extracted_text + "<br><hr>" + additional_details
            
            chat_state['stage'] = 'complete'
            session['chat_state'] = json.dumps(chat_state)
            return jsonify({
                "response": "Perfect! The report is now ready to be generated. Would you like to generate it now?"
            })
        else:
            # User has provided additional information
            chat_state['additional_info'] = user_message
            
            # Update the extracted text with all collected details
            additional_details = ""
            if chat_state.get('collected_details'):
                additional_details += "<br><b>Additional Details:</b><br>" + "<br>".join(
                    [f"<b>{key.replace('_', ' ').title()}:</b> {value}" for key, value in chat_state['collected_details'].items()]
                )
            
            if user_message.strip():
                additional_details += f"<br><b>Additional Information:</b><br>{user_message}"
            
            session['extracted_text'] = extracted_text + "<br><hr>" + additional_details
            
            chat_state['stage'] = 'complete'
            session['chat_state'] = json.dumps(chat_state)
            return jsonify({
                "response": "Thank you for providing that additional information! The report is now ready to be generated. Would you like to generate it now?"
            })
    
    # Complete stage - respond to general questions or commands
    elif chat_state['stage'] == 'complete':
        if 'generate' in user_message.lower() or 'report' in user_message.lower() or 'yes' in user_message.lower():
            return jsonify({
                "response": "Great! You can generate the report by clicking the 'Generate Report' button."
            })
        else:
            # Use Gemini to respond to any other questions based on collected information
            chat_prompt = f"""
            You are an AI chatbot that helps users generate event reports.
            
            <b>Current Event Details:</b><br>{session.get('extracted_text', 'No details available.')}<br><br>
            <b>User Message:</b> {user_message}
            
            Please provide a helpful response based on the event details and the user's message.
            Keep your response concise and focused on the event information.
            """
            
            try:
                chat_response = model.generate_content(chat_prompt)
                return jsonify({"response": chat_response.text})
            except Exception as e:
                return jsonify({"response": f"I'm having trouble processing that. Can you try rephrasing your question? Error: {str(e)}"})
    
    # Default fallback response
    return jsonify({
        "response": "I'm not sure how to respond to that. Would you like to generate the report with the current information?"
    })
@upload_bp.route('/generate_report', methods=['POST'])
def generate_report():
    """Generate a structured event report and overlay it onto a PDF template."""
    extracted_text = session.get('extracted_text', '')
    collected_details = session.get('collected_details', {})

    if not extracted_text and not collected_details:
        return jsonify({"error": "No data available to generate a report."}), 400

    full_details = extracted_text
    if collected_details:
        full_details += "\n\nAdditional Details:\n" + "\n".join(
            [f"{key.replace('_', ' ').title()}: {value}" for key, value in collected_details.items()]
        )

    report_prompt = f"""
Generate a formal event report based on the following details:

{full_details}

### Report Structure:
1. **Title**: Clearly state the event name.
2. **Introduction**: Provide an overview, including date, time, location, and purpose.
3. **Event Highlights**: Cover key moments, important speakers, discussions, and audience interactions.
4. **Main Content**: Describe sessions, activities, and engagements in detail.
5. **Conclusion**: Summarize key takeaways, future implications, and any recommendations.

- The report must be **well-structured**, using paragraphs (not bullet points).
- Use **clear headings** and **subheadings** to organize the content.
- Ensure the report is **coherent, engaging, and written in the past tense**.
"""

    try:
        response = model.generate_content(report_prompt)
        report_text = response.text if response.text else "Failed to generate report."
    except Exception as e:
        return jsonify({"error": f"Report generation failed: {str(e)}"}), 500

    upload_folder = os.path.abspath(app.config['UPLOAD_FOLDER'])
    os.makedirs(upload_folder, exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    output_pdf_filename = f"Event_Report_{timestamp}.pdf"
    output_pdf_path = os.path.join(upload_folder, output_pdf_filename)

    try:
        template_reader = PdfReader(TEMPLATE_PATH)
        pdf_writer = PdfWriter()
        total_template_pages = len(template_reader.pages)

        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)

        heading_font = "Helvetica-Bold"
        body_font = "Helvetica"

        # Margins and text positions
        x_margin = 50
        y_start_page1 = 680  # First page (lowered to avoid title overlap)
        y_start_page2 = 705  # Second page (higher, since no title)
        line_height = 18
        max_width = 500
        max_lines_per_page = 36  # Adjusted for header/footer space

        def wrap_text(canvas_obj, text, max_width, max_lines):
            paragraphs = text.split("\n")
            pages = []
            current_page = []

            for para in paragraphs:
                if para.strip():
                    is_bold = para.startswith("**") and para.endswith("**")
                    if is_bold:
                        para = para.strip("**")
                        canvas_obj.setFont(heading_font, 14)
                    else:
                        canvas_obj.setFont(body_font, 12)

                    wrapped_lines = simpleSplit(para, canvas_obj._fontname, canvas_obj._fontsize, max_width)

                    for line in wrapped_lines:
                        if len(current_page) >= max_lines:
                            pages.append(current_page)
                            current_page = []
                        current_page.append((line, is_bold))

            if current_page:
                pages.append(current_page)

            return pages

        text_pages = wrap_text(can, report_text, max_width, max_lines_per_page)

        for page_index, text_lines in enumerate(text_pages):
            if page_index > 0:
                can.showPage()
                can.setFont(body_font, 12)

            # Adjust y_position based on the page number
            y_position = y_start_page1 if page_index == 0 else y_start_page2

            for line, is_bold in text_lines:
                if is_bold:
                    can.setFont(heading_font, 14)
                else:
                    can.setFont(body_font, 12)

                can.drawString(x_margin, y_position, line)
                y_position -= line_height

        can.save()
        packet.seek(0)

        overlay_reader = PdfReader(packet)

        for page_index in range(len(text_pages)):
            template_page_index = min(page_index, total_template_pages - 1)
            template_page = template_reader.pages[template_page_index]

            new_page = template_page  # Copy the selected template page
            new_page.merge_page(overlay_reader.pages[page_index])
            pdf_writer.add_page(new_page)

        with open(output_pdf_path, "wb") as output_pdf:
            pdf_writer.write(output_pdf)

        if not os.path.exists(output_pdf_path):
            return jsonify({"error": "PDF generation failed. File not found."}), 500

    except Exception as e:
        return jsonify({"error": f"PDF processing failed: {str(e)}"}), 500

    return jsonify({"success": True, "preview_url": f"/preview/{output_pdf_filename}", "edit_url": f"/edit_report/{output_pdf_filename}"})

@upload_bp.route('/preview/<filename>', methods=['GET'])
def preview_file(filename):
    """Serve the generated PDF for preview instead of downloading."""
    upload_folder = os.path.abspath(app.config['UPLOAD_FOLDER'])
    pdf_path = os.path.join(upload_folder, filename)
    if os.path.exists(pdf_path):
        return send_file(pdf_path, mimetype="application/pdf")
    else:
        return jsonify({"error": "File not found"}), 404


@upload_bp.route('/edit_report/<filename>', methods=['GET'])
def edit_report(filename):
    """Render an editable report view."""
    upload_folder = os.path.abspath(app.config['UPLOAD_FOLDER'])
    pdf_path = os.path.join(upload_folder, filename)
    if os.path.exists(pdf_path):
        return render_template('edit_report.html', pdf_url=f"/preview/{filename}")
    else:
        return jsonify({"error": "File not found"}), 404

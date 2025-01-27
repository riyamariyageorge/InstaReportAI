from flask import Flask, Blueprint, request, jsonify, render_template
import base64
import google.generativeai as genai
import os
from werkzeug.utils import secure_filename
from datetime import datetime
#import json
from dotenv import load_dotenv
app = Flask(__name__)
upload_bp = Blueprint('upload_bp', __name__, template_folder='../templates', static_folder='../static')
load_dotenv()

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
genai_api_key=os.getenv('GEMINI_API_KEY')
genai.configure(api_key=genai_api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_bp.route('/upload2', methods=['GET'])
def show_upload_page():
    return render_template('upload2.html')


@upload_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            with open(filepath, "rb") as doc_file:
                doc_data = base64.b64encode(doc_file.read()).decode("utf-8")

            mime_type = 'application/pdf' if filename.endswith('.pdf') else 'image/jpeg'

            summary_prompt = """
            Extract all event-related information from this document including:
            - Event title, date, time, venue
            - Organizers and collaborators
            - Speakers and their credentials
            - Program flow and activities
            - Participant details
            - Key outcomes and highlights
            - Any other relevant details
            
            Present the information in clear, detailed paragraphs using Markdown.
            """
            
            response = model.generate_content([
                {'mime_type': mime_type, 'data': doc_data},
                summary_prompt
            ])

            os.remove(filepath)

            return jsonify({
                'status': 'success',
                'summary': response.text,
                'filename': filename,
                'timestamp': datetime.now().isoformat()
            })

        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'Invalid file type'}), 400

@upload_bp.route('/chat', methods=['POST'])
def chat():
    try:
        # Extract data from the user's request
        data = request.json
        user_input = data.get('message', '')
        contexts = data.get('contexts', [])

        # Format the contexts from uploaded documents
        formatted_contexts = []
        for context in contexts:
            formatted_contexts.append(f"Document Content:\n{context}\n{'='*40}")
        
        # Combine contexts into a single string or use a fallback message if no documents are uploaded
        combined_context = "\n".join(formatted_contexts) if contexts else "No uploaded documents provided."

        # Create a prompt with instructions to ask the user for further input if required
        prompt = f"""
        Based on these document(s):
        {combined_context}

        User Question: {user_input}

        Please provide a detailed response that:
        1. Accurately reflects information from the documents, if available.
        2. Incorporates the user's input when the documents do not contain certain details.
        3. Asks the user whether they would like to add more information or clarify any missing details.
        4. Suggests additional details (if necessary) to enhance the completeness of the event report.
        5. Uses proper formatting for readability.
        """

        # Generate response using the model
        response = model.generate_content(prompt)

        # Return the model's response and ask the user if they would like to add more details
        return jsonify({
            'response': response.text + "\n\nWould you like to add any further details or clarify additional aspects of the event?",
            'status': 'success'
        })

    except Exception as e:
        # Handle errors gracefully and provide feedback to the user
        return jsonify({'error': str(e)}), 500


@upload_bp.route('/generate-report', methods=['POST'])
def generate_report():
    try:
        data = request.json
        contexts = data.get('contexts', [])
        chat_history = data.get('chatHistory', [])
        files = data.get('files', [])

        document_list = '\n'.join([f"- {file}" for file in files])
        
        formatted_contexts = []
        for i, context in enumerate(contexts):
            formatted_contexts.append(f"Document {i+1}:\n{context}\n{'='*40}")
        context_summary = '\n'.join(formatted_contexts)
        
        chat_insights = '\n'.join([
            f"Discussion Point: {chat['question']}\nResponse: {chat['answer']}\n{'-'*40}"
            for chat in chat_history
        ])

        report_prompt = f"""
        Based on the following information, create a comprehensive post-event report:

        *Source Documents:*
        {document_list}

        *Detailed Content:*
        {context_summary}

        *Discussion Points:*
        {chat_insights}

        Create a detailed report that:
        1. Reads like a post-event narrative (use past tense)
        2. Begins with an compelling introduction about the event
        3. Follows a natural flow of information
        4. Includes all relevant details about:
           - The event's purpose and significance
           - Proceedings and key moments
           - Participant engagement
           - Notable outcomes
           - Closing remarks
        5. Concludes with the event's impact and achievements
        
        Guidelines:
        - Write in a professional yet engaging style
        - Use clear, descriptive headings where appropriate
        - Include specific details, names, and facts from the documents
        - Incorporate relevant discussion points naturally into the narrative
        - Focus on creating a coherent, well-structured narrative
        - Use proper Markdown formatting for readability
        
        Note: The report should read like a comprehensive summary of an event that has already taken place, 
        maintaining professionalism while capturing the event's significance and outcomes.
        """

        response = model.generate_content(report_prompt)

        return jsonify({
            'status': 'success',
            'report': response.text,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


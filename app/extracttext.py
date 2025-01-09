import google.generativeai as genai
import base64
import json
from dotenv import load_dotenv
import os

load_dotenv()  # Load .env variables

GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("API key not found. Please check your .env file.")

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

def extract_event_details(image_path):
    try:
        # Read and encode image
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')

        # Define the prompt
        prompt = (
            "Analyze this text and return only a JSON object with these fields: "
            "event_name, date, time, venue. If any field is not found, set it to null.\n\n"
        )

        # Initialize the model
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Generate content
        response = model.generate_content([
            {'mime_type': 'image/jpeg', 'data': image_data},
            prompt
        ])

        # Debug: Log response
        print(f"Raw Response: {response}")

        # Check if the response is valid and has text
        if response and response.text:
            # Extract the text and remove Markdown code fences if present
            raw_text = response.text.strip()
            if raw_text.startswith("```") and raw_text.endswith("```"):
                # Remove the leading and trailing code fences
                raw_text = raw_text.split("\n", 1)[1].rsplit("\n", 1)[0]
            '''
            print(f"Cleaned Response Text: {raw_text}")
            # Attempt to parse JSON from cleaned text
            extracted_data = json.loads(raw_text)
            print(f"Extracted Data: {extracted_data}")
            event_name = extracted_data.get('event_name')
            date = extracted_data.get('date')
            time = extracted_data.get('time')
            venue = extracted_data.get('venue')
            '''
            extracted_data = json.loads(raw_text)
            return {
                'event_name': extracted_data.get('event_name'),
                'date': extracted_data.get('date'),
                'time': extracted_data.get('time'),
                'venue': extracted_data.get('venue')
         }
        else:
            return None
    except Exception as e:
        print(f"Error during extraction: {e}")
        return None
'''
    except json.JSONDecodeError:
        print("Error: Unable to parse JSON from response text.")
        return None
'''
    

import easyocr
import spacy
import re
from datetime import datetime

# Load SpaCy model (pre-trained English model)
nlp = spacy.load("en_core_web_sm")

# Initialize EasyOCR Reader for English
reader = easyocr.Reader(['en'])

# Function to extract text from the poster using EasyOCR
def extract_text_from_image(image_path):
    result = reader.readtext(image_path, detail=0)  # Extract text without details
    extracted_text = " ".join(result)  # Combine the extracted text into a single string
    return extracted_text

# Function to identify and format date and time

def format_date(date_text):
    try:
        # Try parsing the date text in different formats
        formats = ["%d %B %Y", "%B %d", "%d-%B-%Y", "%B %d, %Y"]
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_text, fmt)
                return parsed_date.strftime("%d %B %Y")
            except ValueError:
                continue
    except Exception as e:
        pass
    return date_text

def format_time(time_text):
    try:
        # Try parsing the time text in different formats
        formats = ["%I:%M %p", "%I %p", "%H:%M"]
        for fmt in formats:
            try:
                parsed_time = datetime.strptime(time_text.upper(), fmt)
                return parsed_time.strftime("%I:%M %p")
            except ValueError:
                continue
    except Exception as e:
        pass
    return time_text

# Function to identify the necessary data (event title, date, venue) using SpaCy NER and regex
def identify_event_data(text):
    doc = nlp(text)

    event_data = {
        "title": None,
        "date": None,
        "time": None,
        "venue": None
    }

    # Basic regex patterns for date and time extraction
    date_pattern = r'\b(?:\d{1,2}(?:th|st|nd|rd)?[-\s][A-Za-z]+\s\d{2,4}|\b[A-Za-z]+\s*\d{1,2}\b)'
    time_pattern = r'\b\d{1,2}:\d{2}\s*[apAP][mM]|\b\d{1,2}\s*[apAP][mM]|\b\d{1,2}[-:]\d{2}\s*[apAP][mM]'
    title_pattern = r'([A-Z][A-Z\s]+)'

    # Extract entities using SpaCy
    for ent in doc.ents:
        if ent.label_ == "EVENT":
            event_data["title"] = ent.text
        elif ent.label_ == "DATE":
            event_data["date"] = format_date(ent.text)
        elif ent.label_ == "TIME":
            event_data["time"] = format_time(ent.text)
        elif ent.label_ == "GPE" or ent.label_ == "LOC":
            event_data["venue"] = ent.text

    # Fallback using regex if NER didn't identify date or venue
    if event_data["date"] is None:
        date_match = re.search(date_pattern, text)
        if date_match:
            event_data["date"] = format_date(date_match.group(0))

    if event_data["time"] is None:
        time_match = re.search(time_pattern, text)
        if time_match:
            event_data["time"] = format_time(time_match.group(0))

    # Simple venue extraction based on common keywords
    if event_data["venue"] is None:
        if "Venue:" in text:
            venue_match = text.split("Venue:")[-1].strip()
            event_data["venue"] = venue_match.split()[0]  # Take first word as venue for simplicity

    if event_data["title"] is None:
        title_match = re.search(title_pattern, text)
        if title_match:
            event_data["title"] = title_match.group(0).strip()

    return event_data

# Function to handle the poster upload and process it
def process_event_poster(image_path):
    # Step 1: Extract text using EasyOCR
    extracted_text = extract_text_from_image(image_path)
    print("Extracted Text:\n", extracted_text)

    # Step 2: Identify event data using SpaCy NER
    event_data = identify_event_data(extracted_text)
    print("\nIdentified Event Data:\n", event_data)

    return event_data
#image_path = "C:/Users/riyav/JupyterNotebook/image.png"
#event_data = process_event_poster(image_path)
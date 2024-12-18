import easyocr
import spacy
import re
from PIL import Image
#from dateutil.parser import parse
from flask import session


# Load SpaCy model (pre-trained English model)
nlp = spacy.load("en_core_web_sm")

# Initialize EasyOCR Reader for English
reader = easyocr.Reader(['en'])

# Function to validate and standardize the date format
def validate_date(date_str):
    try:
        # Try to parse and return the date in a standard format
        return parse(date_str).strftime("%d/%m/%Y")  # Format: DD/MM/YYYY
    except ValueError:
        # If parsing fails, return None
        return None

# Function to extract text from the poster using EasyOCR
def extract_text_from_image(image_path):
    result = reader.readtext(image_path, detail=0)  # Extract text without details
    extracted_text = " ".join(result)  # Combine the extracted text into a single string
    return extracted_text

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
    date_pattern = r'\b(?:\d{1,2}\s*[A-Za-z]+\s*\d{4}|\d{1,2}\s*[A-Za-z]+[-,]?\s*\d{4}|\d{1,2}\s*[A-Za-z]{3,9}\s*\d{4})\b'
    time_pattern = r'\b\d{1,2}[:.]\d{2}\s*[apAP][mM]|\b\d{1,2}\s*[apAP][mM]|\b\d{1,2}[-:]\d{2}\s*[apAP][mM]'
    title_pattern = r'([A-Z][A-Za-z0-9\s,:-]{5,100})'  # This pattern should match titles more effectively
    venue_pattern = r'(?i)(?:Venue\s*[:\-]?\s*)(.*)'

    # Extract entities using SpaCy
    for ent in doc.ents:
        if ent.label_ == "EVENT":
            event_data["title"] = ent.text
        elif ent.label_ == "DATE":
            event_data["date"] = ent.text
        elif ent.label_ == "TIME":
            event_data["time"] = ent.text
        elif ent.label_ in ["GPE", "LOC"]:
            event_data["venue"] = ent.text

    # Fallback to regex for missing fields
    if not event_data["date"]:
        date_match = re.search(date_pattern, text)
        if date_match:
            event_data["date"] = validate_date(date_match.group(0)) or date_match.group(0)

    if not event_data["time"]:
        time_match = re.search(time_pattern, text)
        if time_match:
            event_data["time"] = time_match.group(0)  # No standardization for now

    if not event_data["venue"]:
        venue_match = re.search(venue_pattern, text)
        if venue_match:
            event_data["venue"] = venue_match.group(1).strip()

    if not event_data["title"]:
        title_match = re.search(title_pattern, text)
        if title_match:
            # Remove prefix such as 'Presented by:'
            title = title_match.group(0).strip()
            if title.lower().startswith('presented by:'):
                event_data["title"] = title.replace("Presented by:", "").strip()
            else:
                event_data["title"] = title

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




# Example usage (replace 'path_to_your_image' with the actual image file path)
#image_path = list(uploaded.keys())[0]
#image_path = "C:/Users/riyav/JupyterNotebook/img1.png"
#event_data = process_event_poster(image_path)


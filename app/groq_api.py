#import requests
import os
from dotenv import load_dotenv
from groq import Groq

#GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

load_dotenv()
client = Groq(api_key = os.getenv("GROQ_API_KEY"))
def generate_event_description(event_data):
    try:
        input_text = (
            f"Generate a short, professional event report from the following details:\n\n"
            f"Event Title: {event_data['event_name']}\n"
            f"Date: {event_data['date']}\n"
            f"Time: {event_data['time']}\n"
            f"Venue: {event_data['venue']}\n\n"
            "The description should be concise."
        )
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": input_text}
            ],
            model="llama-3.3-70b-versatile",

            temperature=0.5,
            max_tokens=200,
            top_p=1,
            stop=None,
            stream=False,
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating description: {e}")
        return "Unable to generate a description at this time."

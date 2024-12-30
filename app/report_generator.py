import requests
import os

def generate_report_with_groq(prompt):
    """
    Interact with the Groq API to generate a report based on the prompt.
    """
    api_key = os.getenv("GROQ_API_KEY")  # Get API key from environment variables
    model_name = "llama-3.1"  # Use Groq's Llama model, you can change to other versions like llama-3.2
    
    url = f"https://api.groq.ai/v1/generate"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model_name,
        "input": prompt,
        "max_length": 700
    }
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("generated_text", "")
    else:
        raise Exception(f"Error from Groq API: {response.text}")

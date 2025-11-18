# gemini_client.py

import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai import Client

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

# create global client
client = Client(api_key=API_KEY)

def ask_gemini(prompt: str):
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        # response.text = auto stitched text
        return response.text

    except Exception as e:
        print("❌ Gemini ERROR:", e)
        return None

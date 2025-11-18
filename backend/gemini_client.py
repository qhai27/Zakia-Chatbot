"""
Gemini Client - Fixed for Free API Keys
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=API_KEY)

# Create global model with free tier model
# ✅ gemini-1.5-flash is available on free tier
model = genai.GenerativeModel('gemini-1.5-flash')

def ask_gemini(prompt: str, temperature: float = 0.7, max_tokens: int = 500):
    """
    Simple function to ask Gemini a question
    
    Args:
        prompt: The question/prompt to send to Gemini
        temperature: Creativity level (0.0-1.0)
        max_tokens: Maximum response length
    
    Returns:
        str: Gemini's response text, or None if error
    """
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
        )
        
        # Return the text response
        return response.text
    
    except Exception as e:
        print(f"❌ Gemini ERROR: {e}")
        return None


def test_gemini():
    """
    Test if Gemini is working
    """
    try:
        print("🧪 Testing Gemini API...")
        response = ask_gemini("Say 'Hello from Gemini!' in Malay")
        
        if response:
            print(f"✅ API Working!")
            print(f"   Response: {response}")
            return True
        else:
            print("❌ No response from API")
            return False
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    # Run test when script is executed directly
    test_gemini()
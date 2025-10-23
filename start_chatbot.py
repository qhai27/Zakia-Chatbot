#!/usr/bin/env python3
"""
ZAKIA Chatbot Startup Script
This script helps you start the chatbot with proper initialization
"""

import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def main():
    print("🤖 ZAKIA Chatbot Startup")
    print("=" * 50)
    
    try:
        # Import and run the Flask app
        from backend.app import app
        
        print("✅ All modules loaded successfully")
        print("🚀 Starting ZAKIA Chatbot...")
        print("📱 Open frontend/index.html in your browser")
        print("🌐 Backend will be available at http://localhost:5000")
        print("=" * 50)
        
        # Run the app
        app.run(host="0.0.0.0", port=5000, debug=True)
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Please make sure you're in the correct directory and all dependencies are installed.")
        print("Run: pip install -r backend/requirement.txt")
        
    except Exception as e:
        print(f"❌ Error starting chatbot: {e}")
        print("Please check your MySQL connection and try again.")

if __name__ == "__main__":
    main()

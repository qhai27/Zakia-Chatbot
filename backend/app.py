from flask import Flask, request, jsonify
from flask_cors import CORS
import difflib
import uuid
from database import DatabaseManager

app = Flask(__name__)
CORS(app)  # Allow frontend connection

# Initialize database
db = DatabaseManager()

@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_input = request.json.get("message", "").strip()
        session_id = request.json.get("session_id", str(uuid.uuid4()))
        
        if not user_input:
            return jsonify({"reply": "Sila masukkan soalan anda."})
        
        # Get FAQs from database
        faqs = db.get_faqs()
        if not faqs:
            return jsonify({"reply": "Maaf, sistem FAQ tidak tersedia buat masa ini."})
        
        # Find best match
        questions = [faq["question"].lower() for faq in faqs]
        closest_match = difflib.get_close_matches(user_input.lower(), questions, n=1, cutoff=0.4)
        
        if closest_match:
            for faq in faqs:
                if faq["question"].lower() == closest_match[0]:
                    response = faq["answer"]
                    # Log the interaction
                    db.log_chat(user_input, response, session_id)
                    return jsonify({
                        "reply": response,
                        "session_id": session_id,
                        "matched_question": faq["question"]
                    })
        
        # No match found
        fallback_response = "Maaf, saya tidak pasti tentang itu. Anda boleh rujuk laman rasmi LZNK untuk maklumat lanjut atau cuba soalan lain."
        db.log_chat(user_input, fallback_response, session_id)
        return jsonify({
            "reply": fallback_response,
            "session_id": session_id
        })
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({"reply": "Maaf, berlaku ralat sistem. Sila cuba lagi."})

@app.route("/faqs", methods=["GET"])
def get_faqs():
    """Get all FAQs"""
    try:
        faqs = db.get_faqs()
        return jsonify({"faqs": faqs})
    except Exception as e:
        print(f"Error fetching FAQs: {e}")
        return jsonify({"faqs": []})

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "LZNK Chatbot is running"})

if __name__ == "__main__":
    # Initialize database
    if db.create_database():
        if db.connect():
            db.create_tables()
            db.insert_faqs()
            print("Database initialized successfully")
        else:
            print("Failed to connect to database")
    else:
        print("Failed to create database")
    
    app.run(host="0.0.0.0", port=5000, debug=True)
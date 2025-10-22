from flask import Flask, request, jsonify
from flask_cors import CORS
import difflib
import uuid
from database import DatabaseManager
from nlp_processor import NLPProcessor

app = Flask(__name__)
CORS(app)  # Allow frontend connection

# Initialize database and NLP processor
db = DatabaseManager()
nlp = NLPProcessor()

@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_input = request.json.get("message", "").strip()
        session_id = request.json.get("session_id", str(uuid.uuid4()))
        
        if not user_input:
            return jsonify({"reply": "Sila masukkan soalan anda."})
        
        # Analyze user intent
        intent = nlp.analyze_user_intent(user_input)
        
        # Handle greetings
        if intent['is_greeting']:
            greeting_responses = [
                "Assalamualaikum! 👋 Saya ZAKIA dari LZNK. Bagaimana saya boleh membantu anda hari ini?",
                "Assalamualaikum! 😊 Selamat datang ke LZNK Chat Support. Apa yang boleh saya bantu?",
                "Assalamualaikum! 👋 Saya di sini untuk membantu anda dengan soalan tentang zakat dan LZNK."
            ]
            greeting_response = greeting_responses[0]  # You can randomize this
            db.log_chat(user_input, greeting_response, session_id)
            return jsonify({
                "reply": greeting_response,
                "session_id": session_id,
                "intent": "greeting"
            })
        
        # Handle thanks
        if intent['is_thanks']:
            thanks_responses = [
                "Sama-sama! 😊 Adakah ada lagi yang ingin anda tanya tentang zakat atau LZNK?",
                "Terima kasih! 😊 Saya gembira dapat membantu. Ada lagi yang ingin ditanya?",
                "Sama-sama! 😊 Saya di sini untuk membantu. Apa lagi yang boleh saya bantu?"
            ]
            thanks_response = thanks_responses[0]
            db.log_chat(user_input, thanks_response, session_id)
            return jsonify({
                "reply": thanks_response,
                "session_id": session_id,
                "intent": "thanks"
            })
        
        # Handle goodbye
        if intent['is_goodbye']:
            goodbye_responses = [
                "Terima kasih! Semoga bermanfaat. Jumpa lagi! 👋",
                "Selamat tinggal! 😊 Semoga zakat anda diterima. Jumpa lagi!",
                "Terima kasih! 😊 Saya gembira dapat membantu. Selamat tinggal!"
            ]
            goodbye_response = goodbye_responses[0]
            db.log_chat(user_input, goodbye_response, session_id)
            return jsonify({
                "reply": goodbye_response,
                "session_id": session_id,
                "intent": "goodbye"
            })
        
        # Handle help requests
        if intent['is_help_request']:
            help_response = "Saya di sini untuk membantu! 😊 Anda boleh bertanya tentang zakat, LZNK, cara pembayaran, nisab, atau program bantuan. Apa yang ingin anda tahu?"
            db.log_chat(user_input, help_response, session_id)
            return jsonify({
                "reply": help_response,
                "session_id": session_id,
                "intent": "help_request"
            })
        
        # Handle complaints
        if intent['is_complaint']:
            complaint_response = "Maaf atas masalah yang anda hadapi. 🙏 Saya akan cuba membantu. Bolehkah anda jelaskan masalah anda dengan lebih terperinci? Atau anda boleh menghubungi LZNK secara langsung."
            db.log_chat(user_input, complaint_response, session_id)
            return jsonify({
                "reply": complaint_response,
                "session_id": session_id,
                "intent": "complaint"
            })
        
        # Handle praise
        if intent['is_praise']:
            praise_response = "Terima kasih! 😊 Saya gembira dapat membantu. Adakah ada lagi yang ingin anda tanya tentang zakat atau LZNK?"
            db.log_chat(user_input, praise_response, session_id)
            return jsonify({
                "reply": praise_response,
                "session_id": session_id,
                "intent": "praise"
            })
        
        # Handle confused users
        if intent['is_confused']:
            confused_response = "Tidak mengapa, saya di sini untuk membantu! 😊 Bolehkah anda cuba bertanya dengan cara yang berbeza? Atau anda boleh bertanya tentang topik zakat yang lain seperti nisab, cara pembayaran, atau program LZNK."
            db.log_chat(user_input, confused_response, session_id)
            return jsonify({
                "reply": confused_response,
                "session_id": session_id,
                "intent": "confused"
            })
        
        # Get FAQs from database
        faqs = db.get_faqs()
        if not faqs:
            return jsonify({"reply": "Maaf, sistem FAQ tidak tersedia buat masa ini."})
        
        # Use NLP processor to find best match
        response_data = nlp.generate_response(user_input, faqs, threshold=0.3)
        
        # Log the interaction
        db.log_chat(user_input, response_data['reply'], session_id)
        
        return jsonify({
            "reply": response_data['reply'],
            "session_id": session_id,
            "matched_question": response_data.get('matched_question'),
            "confidence": response_data.get('confidence', 0.0),
            "category": response_data.get('category', 'Unknown'),
            "intent": intent
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

# -----------------------------
# Admin FAQ CRUD endpoints (no auth; for internal use)
# Base path: /admin/faqs
# -----------------------------

@app.route("/admin/faqs", methods=["GET"])
def admin_list_faqs():
    try:
        faqs = db.get_faqs()
        return jsonify({"faqs": faqs})
    except Exception as e:
        print(f"Error listing FAQs: {e}")
        return jsonify({"faqs": []}), 500


@app.route("/admin/faqs/<int:faq_id>", methods=["GET"])
def admin_get_faq(faq_id):
    try:
        faq = db.get_faq_by_id(faq_id)
        if not faq:
            return jsonify({"error": "Not found"}), 404
        return jsonify({"faq": faq})
    except Exception as e:
        print(f"Error getting FAQ: {e}")
        return jsonify({"error": "Server error"}), 500


@app.route("/admin/faqs", methods=["POST"])
def admin_create_faq():
    try:
        data = request.get_json(force=True) or {}
        question = (data.get("question") or "").strip()
        answer = (data.get("answer") or "").strip()
        category = (data.get("category") or None)
        if not question or not answer:
            return jsonify({"error": "'question' and 'answer' are required"}), 400
        new_id = db.create_faq(question, answer, category)
        if not new_id:
            return jsonify({"error": "Failed to create"}), 500
        faq = db.get_faq_by_id(new_id)
        return jsonify({"faq": faq}), 201
    except Exception as e:
        print(f"Error creating FAQ: {e}")
        return jsonify({"error": "Server error"}), 500


@app.route("/admin/faqs/<int:faq_id>", methods=["PUT", "PATCH"])
def admin_update_faq(faq_id):
    try:
        data = request.get_json(force=True) or {}
        # If partial, fetch existing first
        existing = db.get_faq_by_id(faq_id)
        if not existing:
            return jsonify({"error": "Not found"}), 404
        question = (data.get("question") or existing.get("question") or "").strip()
        answer = (data.get("answer") or existing.get("answer") or "").strip()
        category = data.get("category") if "category" in data else existing.get("category")
        if not question or not answer:
            return jsonify({"error": "'question' and 'answer' are required"}), 400
        ok = db.update_faq(faq_id, question, answer, category)
        if not ok:
            return jsonify({"error": "Failed to update"}), 500
        faq = db.get_faq_by_id(faq_id)
        return jsonify({"faq": faq})
    except Exception as e:
        print(f"Error updating FAQ: {e}")
        return jsonify({"error": "Server error"}), 500


@app.route("/admin/faqs/<int:faq_id>", methods=["DELETE"])
def admin_delete_faq(faq_id):
    try:
        existing = db.get_faq_by_id(faq_id)
        if not existing:
            return jsonify({"error": "Not found"}), 404
        ok = db.delete_faq(faq_id)
        if not ok:
            return jsonify({"error": "Failed to delete"}), 500
        return jsonify({"deleted": True, "id": faq_id})
    except Exception as e:
        print(f"Error deleting FAQ: {e}")
        return jsonify({"error": "Server error"}), 500

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
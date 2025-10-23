from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
from database import DatabaseManager
from enhanced_nlp import EnhancedNLPProcessor

app = Flask(__name__)
CORS(app)

# Initialize database and enhanced NLP processor
db = DatabaseManager()
nlp = EnhancedNLPProcessor()

def initialize_nlp():
    """Initialize and train the NLP model"""
    print("🚀 Initializing Enhanced NLP model...")
    
    if nlp.load_training_data('training_data.json'):
        print("✅ Loaded pre-trained model")
    else:
        print("📚 Training model from FAQ data...")
        faqs = db.get_faqs()
        if faqs:
            nlp.train_from_faqs(faqs)
            nlp.save_training_data('training_data.json')
            print("✅ Model trained and saved")
        else:
            print("⚠️ No FAQ data available for training")

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
                "Hello! 😊 Welcome to LZNK Chat Support. How may I help you today?",
                "Assalamualaikum! 👋 Saya di sini untuk membantu anda dengan soalan tentang zakat dan LZNK."
            ]
            
            # Detect language
            text_lower = user_input.lower()
            if any(word in text_lower for word in ['hello', 'hi', 'good morning']):
                greeting_response = greeting_responses[1]
            else:
                greeting_response = greeting_responses[0]
            
            nlp.add_to_context(session_id, greeting_response, 'bot')
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
                "You're welcome! 😊 Is there anything else you'd like to know about zakat or LZNK?",
                "Terima kasih! 😊 Saya gembira dapat membantu. Ada lagi yang boleh saya bantu?"
            ]
            
            # Detect language from previous context
            history = nlp.get_conversation_history(session_id)
            use_english = any('hello' in msg['message'].lower() or 'hi' in msg['message'].lower() 
                            for msg in history if msg['role'] == 'user')
            
            thanks_response = thanks_responses[1] if use_english else thanks_responses[0]
            nlp.add_to_context(session_id, thanks_response, 'bot')
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
                "Thank you! Have a great day. See you again! 👋",
                "Selamat tinggal! 😊 Semoga zakat anda diterima. Jumpa lagi!"
            ]
            
            history = nlp.get_conversation_history(session_id)
            use_english = any('hello' in msg['message'].lower() or 'bye' in msg['message'].lower() 
                            for msg in history if msg['role'] == 'user')
            
            goodbye_response = goodbye_responses[1] if use_english else goodbye_responses[0]
            nlp.add_to_context(session_id, goodbye_response, 'bot')
            db.log_chat(user_input, goodbye_response, session_id)
            
            # Clear context after goodbye
            nlp.clear_session_context(session_id)
            
            return jsonify({
                "reply": goodbye_response,
                "session_id": session_id,
                "intent": "goodbye"
            })
        
        # Get FAQs from database
        faqs = db.get_faqs()
        if not faqs:
            return jsonify({"reply": "Maaf, sistem FAQ tidak tersedia buat masa ini."})
        
        # Use enhanced NLP processor with context awareness
        response_data = nlp.generate_response(
            user_input, 
            faqs, 
            session_id=session_id,
            threshold=0.35
        )
        
        # Log the interaction
        db.log_chat(user_input, response_data['reply'], session_id)
        
        # Return enhanced response with confidence metrics
        return jsonify({
            "reply": response_data['reply'],
            "session_id": session_id,
            "matched_question": response_data.get('matched_question'),
            "confidence": response_data.get('confidence', 0.0),
            "confidence_level": response_data.get('confidence_level', 'none'),
            "category": response_data.get('category', 'Unknown'),
            "intent": intent,
            "context_aware": True
        })
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"reply": "Maaf, berlaku ralat sistem. Sila cuba lagi."})

@app.route("/chat/history/<session_id>", methods=["GET"])
def get_chat_history(session_id):
    """Get conversation history for a session"""
    try:
        history = nlp.get_conversation_history(session_id)
        return jsonify({
            "session_id": session_id,
            "history": history,
            "message_count": len(history)
        })
    except Exception as e:
        print(f"Error fetching chat history: {e}")
        return jsonify({"error": "Failed to fetch history"}), 500

@app.route("/chat/clear/<session_id>", methods=["POST"])
def clear_chat_context(session_id):
    """Clear conversation context for a session"""
    try:
        nlp.clear_session_context(session_id)
        return jsonify({
            "message": "Context cleared successfully",
            "session_id": session_id
        })
    except Exception as e:
        print(f"Error clearing context: {e}")
        return jsonify({"error": "Failed to clear context"}), 500

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
    return jsonify({
        "status": "healthy", 
        "message": "LZNK Enhanced Chatbot is running",
        "nlp_trained": len(nlp.training_pairs) > 0,
        "keywords_indexed": len(nlp.keyword_index),
        "active_sessions": len(nlp.conversation_history),
        "version": "2.0 (Context-Aware)"
    })

@app.route("/retrain", methods=["POST"])
def retrain_model():
    """Retrain the NLP model with current FAQ data"""
    try:
        faqs = db.get_faqs()
        if not faqs:
            return jsonify({"error": "No FAQ data available"}), 400
        
        nlp.train_from_faqs(faqs)
        nlp.save_training_data('training_data.json')
        
        return jsonify({
            "message": "Model retrained successfully",
            "faqs_count": len(faqs),
            "keywords_indexed": len(nlp.keyword_index)
        })
    except Exception as e:
        print(f"Error retraining model: {e}")
        return jsonify({"error": "Failed to retrain model"}), 500

# Admin FAQ CRUD endpoints
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
        
        # Retrain model after adding new FAQ
        faqs = db.get_faqs()
        nlp.train_from_faqs(faqs)
        
        faq = db.get_faq_by_id(new_id)
        return jsonify({"faq": faq}), 201
    except Exception as e:
        print(f"Error creating FAQ: {e}")
        return jsonify({"error": "Server error"}), 500

@app.route("/admin/faqs/<int:faq_id>", methods=["PUT", "PATCH"])
def admin_update_faq(faq_id):
    try:
        data = request.get_json(force=True) or {}
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
        
        # Retrain model after updating FAQ
        faqs = db.get_faqs()
        nlp.train_from_faqs(faqs)
        
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
        
        # Retrain model after deleting FAQ
        faqs = db.get_faqs()
        nlp.train_from_faqs(faqs)
        
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
            print("✅ Database initialized successfully")
            
            # Initialize and train enhanced NLP model
            initialize_nlp()
        else:
            print("❌ Failed to connect to database")
    else:
        print("❌ Failed to create database")
    
    print("\n" + "="*60)
    print("🤖 LZNK Enhanced Chatbot Server")
    print("="*60)
    print("✅ Context-aware conversation")
    print("✅ Multi-language support (Malay/English)")
    print("✅ Natural language understanding")
    print("✅ Follow-up question handling")
    print("="*60 + "\n")
    
    app.run(host="0.0.0.0", port=5000, debug=True)
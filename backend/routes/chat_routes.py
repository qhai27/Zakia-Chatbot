"""
Chat routes for ZAKIA Chatbot
Handles all chat-related endpoints
"""

from flask import Blueprint, request, jsonify
import uuid
from database import DatabaseManager
from nlp_processor import NLPProcessor

# Create blueprint
chat_bp = Blueprint('chat', __name__)

# Initialize components
db = DatabaseManager()
nlp = NLPProcessor()

@chat_bp.route("/chat", methods=["POST"])
def chat():
    """Main chat endpoint"""
    try:
        user_input = request.json.get("message", "").strip()
        session_id = request.json.get("session_id", str(uuid.uuid4()))
        
        if not user_input:
            return jsonify({"reply": "Sila masukkan soalan anda."})
        
        # Ensure database connection
        if not db.connection or not db.connection.is_connected():
            if not db.connect():
                return jsonify({"reply": "Maaf, sistem tidak dapat disambungkan ke pangkalan data."})
        
        # Analyze user intent
        intent = nlp.analyze_user_intent(user_input)
        
        # Handle greetings with language awareness
        if intent['is_greeting']:
            language = intent.get('language', 'malay')
            if language == 'english':
                greeting_responses = [
                    "Hello! 👋 I'm ZAKIA from LZNK. How can I help you today?",
                    "Hi there! 😊 Welcome to LZNK Chat Support. What can I assist you with?",
                    "Hello! 👋 I'm here to help you with questions about zakat and LZNK."
                ]
            else:
                greeting_responses = [
                    "Assalamualaikum! 👋 Saya ZAKIA dari LZNK. Bagaimana saya boleh membantu anda hari ini?",
                    "Assalamualaikum! 😊 Selamat datang ke LZNK Chat Support. Apa yang boleh saya bantu?",
                    "Assalamualaikum! 👋 Saya di sini untuk membantu anda dengan soalan tentang zakat dan LZNK."
                ]
            greeting_response = greeting_responses[0]
            db.log_chat(user_input, greeting_response, session_id)
            return jsonify({
                "reply": greeting_response,
                "session_id": session_id,
                "intent": "greeting",
                "language": language
            })
        
        # Handle thanks with language awareness
        if intent['is_thanks']:
            language = intent.get('language', 'malay')
            if language == 'english':
                thanks_responses = [
                    "You're welcome! 😊 Is there anything else you'd like to know about zakat or LZNK?",
                    "Thank you! 😊 I'm glad I could help. Anything else you'd like to ask?",
                    "You're welcome! 😊 I'm here to help. What else can I assist you with?"
                ]
            else:
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
                "intent": "thanks",
                "language": language
            })
        
        # Handle goodbye with language awareness
        if intent['is_goodbye']:
            language = intent.get('language', 'malay')
            if language == 'english':
                goodbye_responses = [
                    "Thank you! Hope it was helpful. See you again! 👋",
                    "Goodbye! 😊 May your zakat be accepted. See you again!",
                    "Thank you! 😊 I'm glad I could help. Goodbye!"
                ]
            else:
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
                "intent": "goodbye",
                "language": language
            })
        
        # Get FAQs from database
        faqs = db.get_faqs()
        if not faqs:
            return jsonify({"reply": "Maaf, sistem FAQ tidak tersedia buat masa ini."})
        
        # Use enhanced NLP processor to find best match with session context
        response_data = nlp.generate_response(user_input, faqs, session_id=session_id, threshold=0.35)
        
        # Log the interaction
        db.log_chat(user_input, response_data['reply'], session_id)
        
        # Get conversation insights for enhanced context
        conversation_insights = nlp.get_conversation_insights(session_id) if session_id else {}
        
        # Return enhanced response with confidence metrics and context
        return jsonify({
            "reply": response_data['reply'],
            "session_id": session_id,
            "matched_question": response_data.get('matched_question'),
            "confidence": response_data.get('confidence', 0.0),
            "confidence_level": response_data.get('confidence_level', 'none'),
            "category": response_data.get('category', 'Unknown'),
            "intent": intent,
            "context_aware": True,
            "language": intent.get('language', 'malay'),
            "sentiment": intent.get('sentiment', 'neutral'),
            "conversation_insights": conversation_insights,
            "is_followup": intent.get('is_followup', False),
            "conversation_summary": response_data.get('conversation_summary', {})
        })
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({"reply": "Maaf, berlaku ralat sistem. Sila cuba lagi."})

@chat_bp.route("/faqs", methods=["GET"])
def get_faqs():
    """Get all FAQs"""
    try:
        # Ensure database connection
        if not db.connection or not db.connection.is_connected():
            if not db.connect():
                return jsonify({"faqs": [], "error": "Database connection failed"})
        
        faqs = db.get_faqs()
        return jsonify({"faqs": faqs})
    except Exception as e:
        print(f"Error fetching FAQs: {e}")
        return jsonify({"faqs": [], "error": str(e)})

@chat_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy", 
        "message": "LZNK Chatbot is running",
        "nlp_trained": len(nlp.training_pairs) > 0,
        "keywords_indexed": len(nlp.keyword_index)
    })

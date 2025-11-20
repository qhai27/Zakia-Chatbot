"""
Chat Routes - SMART MODE
- Ada FAQ: Gunakan FAQ (strict)
- TIADA FAQ: Gemini jawab berdasarkan pengetahuan zakat
"""

from flask import Blueprint, request, jsonify
import uuid
import traceback
from database import DatabaseManager
from nlp_processor import NLPProcessor
from gemini_service import GeminiService

# Create blueprint
chat_bp = Blueprint('chat', __name__)

# Initialize components
db = DatabaseManager()
nlp = NLPProcessor()

# Initialize Gemini
gemini = None
try:
    gemini = GeminiService()
    print("✅ Gemini SMART MODE enabled")
    print("   - FAQ ada: Gunakan FAQ sahaja")
    print("   - FAQ tiada: Gemini jawab dari pengetahuan zakat")
except Exception as e:
    print(f"⚠️ Gemini not available: {e}")

def add_emoji_if_missing(text: str) -> str:
    """Add emoji if missing"""
    emojis = ['😊', '👋', '🙏', '💰', '📞', '✅', '🤝', '💡']
    if not any(emoji in text for emoji in emojis):
        if any(word in text.lower() for word in ['maaf', 'sorry', 'tidak']):
            return text + " 😊"
        elif any(word in text.lower() for word in ['terima kasih', 'thank']):
            return text + " 😄"
        elif any(word in text.lower() for word in ['hubungi', 'telefon']):
            return text + " 📞"
        else:
            return text + " 😊"
    return text

@chat_bp.route("/chat", methods=["POST"])
def chat():
    """
    Main chat endpoint - SMART MODE
    """
    try:
        # Parse request
        data = request.get_json(silent=True) or {}
        user_input = (data.get("message") or "").strip()
        session_id = data.get("session_id") or str(uuid.uuid4())
        
        if not user_input:
            return jsonify({
                "reply": "Sila masukkan soalan anda. 😊",
                "session_id": session_id
            })
        
        print(f"\n💬 [{session_id[:8]}] User: {user_input}")
        
        # Analyze intent
        intent = nlp.analyze_user_intent(user_input)
        print(f"   🎯 Intent: {intent}")
        
        # Handle greetings
        if intent['is_greeting']:
            if gemini:
                try:
                    greeting = gemini.generate_conversational_response(
                        user_input, 
                        context="User is greeting ZAKIA chatbot"
                    )
                    greeting = add_emoji_if_missing(greeting)
                    response = {
                        "reply": greeting,
                        "session_id": session_id,
                        "intent": "greeting",
                        "enhanced_by_gemini": True
                    }
                except Exception as e:
                    print(f"   ⚠️ Gemini error: {e}")
                    response = {
                        "reply": "Assalamualaikum! 👋 Saya ZAKIA dari LZNK. Bagaimana saya boleh membantu anda? 😊",
                        "session_id": session_id,
                        "intent": "greeting"
                    }
            else:
                response = {
                    "reply": "Assalamualaikum! 👋 Saya ZAKIA dari LZNK. Bagaimana saya boleh membantu anda? 😊",
                    "session_id": session_id,
                    "intent": "greeting"
                }
            
            db.log_chat(user_input, response['reply'], session_id)
            return jsonify(response)
        
        # Handle thanks
        if intent['is_thanks']:
            reply = "Sama-sama! 😊 Saya gembira dapat membantu. Ada lagi soalan?"
            db.log_chat(user_input, reply, session_id)
            return jsonify({
                "reply": reply,
                "session_id": session_id,
                "intent": "thanks"
            })
        
        # Handle goodbye
        if intent['is_goodbye']:
            reply = "Terima kasih! Semoga bermanfaat. Jumpa lagi! 👋"
            db.log_chat(user_input, reply, session_id)
            nlp.clear_session_context(session_id)
            return jsonify({
                "reply": reply,
                "session_id": session_id,
                "intent": "goodbye"
            })
        
        # Ensure database connection
        if not db.connection or not db.connection.is_connected():
            print("   ⚠️ Reconnecting to database...")
            if not db.connect():
                return jsonify({
                    "reply": "Maaf, sistem sedang mengalami masalah. Sila cuba lagi. 😅",
                    "session_id": session_id
                }), 500
        
        # Get FAQs
        faqs = db.get_faqs()
        if not faqs:
            print("   ❌ No FAQs available")
            
            # Use Gemini to answer directly (no FAQ available)
            if gemini:
                try:
                    print("   🤖 No FAQs - Using Gemini knowledge...")
                    reply = gemini.answer_zakat_question(user_input, matched_questions=None)
                    reply = add_emoji_if_missing(reply)
                    
                    db.log_chat(user_input, reply, session_id)
                    return jsonify({
                        "reply": reply,
                        "session_id": session_id,
                        "enhanced_by_gemini": True,
                        "source": "gemini_knowledge",
                        "confidence": 0.0,
                        "matched": False
                    })
                except Exception as e:
                    print(f"   ❌ Gemini error: {e}")
            
            return jsonify({
                "reply": "Maaf, sistem tidak tersedia. Sila hubungi pejabat LZNK di 04-733 6633. 📞",
                "session_id": session_id
            }), 500
        
        print(f"   📚 Loaded {len(faqs)} FAQs")
        
        # Find best FAQ match
        response_data = nlp.generate_response(
            user_input, 
            faqs, 
            session_id=session_id,
            threshold=0.25
        )
        
        confidence = response_data.get('confidence', 0)
        matched_question = response_data.get('matched_question')
        faq_answer = response_data['reply']
        
        print(f"   📊 FAQ Confidence: {confidence:.2f}")
        if matched_question:
            print(f"   ✓ Matched FAQ: {matched_question[:60]}...")
        
        # DECISION TREE
        final_reply = faq_answer
        enhanced_by_gemini = False
        answer_source = "faq"
        
        if gemini:
            try:
                # HIGH CONFIDENCE (0.45+) = FAQ match found - enhance it
                if confidence >= 0.45 and matched_question:
                    print(f"   ✅ Good FAQ match - Enhancing with Gemini...")
                    
                    enhanced_reply = gemini.enhance_faq_response(
                        user_input,
                        faq_answer,
                        context={'matched_question': matched_question, 'confidence': confidence}
                    )
                    
                    # Validate enhancement
                    import re
                    faq_numbers = set(re.findall(r'\d+(?:\.\d+)?', faq_answer))
                    enhanced_numbers = set(re.findall(r'\d+(?:\.\d+)?', enhanced_reply))
                    
                    if enhanced_numbers - faq_numbers:
                        print(f"   ⚠️ Enhancement changed numbers, using FAQ")
                        final_reply = add_emoji_if_missing(faq_answer)
                    else:
                        final_reply = add_emoji_if_missing(enhanced_reply)
                        enhanced_by_gemini = True
                    
                    answer_source = "faq_enhanced"
                
                # MEDIUM CONFIDENCE (0.25-0.44) = Weak FAQ match
                # Use Gemini to answer from knowledge, but mention related FAQ
                elif 0.25 <= confidence < 0.45:
                    print(f"   🤔 Weak FAQ match (confident: {confidence:.2f})")
                    print(f"   🤖 Using Gemini knowledge + suggest FAQ...")
                    
                    similar_questions = response_data.get('similar_questions', [])
                    
                    # Use Gemini's smart answering
                    smart_reply = gemini.answer_zakat_question(
                        user_input,
                        matched_questions=similar_questions
                    )
                    
                    final_reply = add_emoji_if_missing(smart_reply)
                    enhanced_by_gemini = True
                    answer_source = "gemini_knowledge"
                
                # LOW/NO CONFIDENCE (<0.25) = No FAQ match
                # Let Gemini answer from its zakat knowledge
                else:
                    print(f"   ❌ No FAQ match (confidence: {confidence:.2f})")
                    print(f"   🤖 Using Gemini zakat knowledge...")
                    
                    similar_questions = response_data.get('similar_questions', [])
                    
                    # Gemini answers using its knowledge
                    smart_reply = gemini.answer_zakat_question(
                        user_input,
                        matched_questions=similar_questions
                    )
                    
                    final_reply = add_emoji_if_missing(smart_reply)
                    enhanced_by_gemini = True
                    answer_source = "gemini_knowledge"
                
            except Exception as gemini_error:
                print(f"   ❌ Gemini error: {gemini_error}")
                traceback.print_exc()
                final_reply = add_emoji_if_missing(faq_answer)
                enhanced_by_gemini = False
                answer_source = "faq_fallback"
        else:
            print(f"   ℹ️ Gemini not available, using FAQ only")
            final_reply = add_emoji_if_missing(faq_answer)
            answer_source = "faq_only"
        
        # Log chat
        try:
            db.log_chat(user_input, final_reply, session_id)
        except Exception as log_error:
            print(f"   ⚠️ Log error: {log_error}")
        
        # Return response
        return jsonify({
            "reply": final_reply,
            "session_id": session_id,
            "matched_question": matched_question if confidence >= 0.45 else None,
            "confidence": round(confidence, 3),
            "confidence_level": response_data.get('confidence_level', 'none'),
            "category": response_data.get('category', 'Umum'),
            "enhanced_by_gemini": enhanced_by_gemini,
            "answer_source": answer_source,
            "gemini_available": gemini is not None,
            "intent": intent
        })
        
    except Exception as e:
        print(f"\n❌ CHAT ERROR: {e}")
        traceback.print_exc()
        
        return jsonify({
            "reply": "Maaf, berlaku ralat. Sila cuba lagi. 😅",
            "session_id": session_id if 'session_id' in locals() else str(uuid.uuid4()),
            "error": str(e)
        }), 500

@chat_bp.route("/chat/history/<session_id>", methods=["GET"])
def get_chat_history(session_id):
    """Get conversation history"""
    try:
        history = nlp.get_conversation_history(session_id)
        return jsonify({
            "success": True,
            "session_id": session_id,
            "history": history,
            "message_count": len(history)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@chat_bp.route("/chat/clear/<session_id>", methods=["POST"])
def clear_chat_context(session_id):
    """Clear conversation context"""
    try:
        nlp.clear_session_context(session_id)
        return jsonify({
            "success": True,
            "message": "Context cleared",
            "session_id": session_id
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@chat_bp.route("/health", methods=["GET"])
def health_check():
    """Health check"""
    try:
        db_status = "connected" if (db.connection and db.connection.is_connected()) else "disconnected"
        gemini_status = "enabled" if gemini else "disabled"
        nlp_trained = len(nlp.training_pairs) > 0
        
        faq_count = 0
        try:
            if db_status == "connected":
                faq_count = len(db.get_faqs())
        except:
            pass
        
        return jsonify({
            "status": "healthy",
            "message": "ZAKIA Chatbot - SMART MODE",
            "components": {
                "database": {"status": db_status, "faq_count": faq_count},
                "nlp": {
                    "trained": nlp_trained,
                    "training_pairs": len(nlp.training_pairs),
                    "keywords": len(nlp.keyword_index)
                },
                "gemini": {
                    "status": gemini_status,
                    "enabled": gemini is not None,
                    "mode": "smart_fallback",
                    "description": "FAQ tersedia = guna FAQ | FAQ tiada = guna pengetahuan Gemini"
                }
            },
            "version": "4.0 (Smart Mode)",
            "features": [
                "✅ FAQ confidence >= 0.45: Enhance FAQ dengan Gemini",
                "✅ FAQ confidence 0.25-0.44: Gemini jawab + cadang FAQ",
                "✅ FAQ confidence < 0.25: Gemini jawab dari pengetahuan zakat"
            ]
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@chat_bp.route("/test-gemini", methods=["GET"])
def test_gemini():
    """Test Gemini"""
    if not gemini:
        return jsonify({
            "success": False,
            "message": "Gemini not initialized"
        }), 503
    
    try:
        result = gemini.test_connection()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@chat_bp.route("/test-smart-mode", methods=["POST"])
def test_smart_mode():
    """
    Test Smart Mode with sample questions
    """
    try:
        data = request.get_json(silent=True) or {}
        test_question = data.get("question", "Apa itu haul dalam zakat?")
        
        print(f"\n🧪 TESTING SMART MODE")
        print(f"   Question: {test_question}")
        
        if not gemini:
            return jsonify({
                "error": "Gemini not available",
                "question": test_question
            }), 503
        
        # Get FAQs
        faqs = db.get_faqs() if db.connection else []
        
        # Try to match FAQ
        if faqs:
            response_data = nlp.generate_response(test_question, faqs, threshold=0.25)
            confidence = response_data.get('confidence', 0)
            matched_faq = response_data.get('matched_question')
            
            print(f"   FAQ Confidence: {confidence:.2f}")
            print(f"   Matched FAQ: {matched_faq or 'None'}")
        else:
            confidence = 0.0
            matched_faq = None
        
        # Test Gemini smart answer
        similar_questions = response_data.get('similar_questions', []) if faqs else []
        gemini_answer = gemini.answer_zakat_question(test_question, similar_questions)
        
        print(f"   Gemini Answer: {gemini_answer[:100]}...")
        
        return jsonify({
            "success": True,
            "test_question": test_question,
            "faq_confidence": round(confidence, 3),
            "matched_faq": matched_faq,
            "gemini_answer": gemini_answer,
            "similar_questions": similar_questions,
            "answer_mode": (
                "faq_enhanced" if confidence >= 0.45 else
                "gemini_with_suggestions" if 0.25 <= confidence < 0.45 else
                "gemini_knowledge"
            )
        })
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
@chat_bp.route("/faqs", methods=["GET"])
def list_faqs():
    try:
        if not db.connect():
            return jsonify({"error": "DB not connected"}), 500

        faqs = db.get_faqs()
        return jsonify({
            "success": True,
            "count": len(faqs),
            "faqs": faqs
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

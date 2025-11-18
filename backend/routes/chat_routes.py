"""
Chat Routes with Always-On Gemini Integration
Gemini is used for ALL responses to ensure natural, accurate answers
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

# Initialize Gemini (with error handling)
gemini = None
try:
    gemini = GeminiService()
    print("✅ Gemini service enabled - ALL responses will be AI-enhanced")
except Exception as e:
    print(f"⚠️ Gemini service not available: {e}")
    print("   Chatbot will work with standard FAQ responses only")

@chat_bp.route("/chat", methods=["POST"])
def chat():
    """
    Main chat endpoint with ALWAYS-ON Gemini AI
    Every response goes through Gemini for natural, accurate answers
    """
    try:
        # Parse request
        data = request.get_json(silent=True) or {}
        user_input = (data.get("message") or "").strip()
        session_id = data.get("session_id") or str(uuid.uuid4())
        
        if not user_input:
            return jsonify({
                "reply": "Sila masukkan soalan anda.",
                "session_id": session_id
            })
        
        print(f"\n💬 [{session_id[:8]}] User: {user_input}")
        
        # Analyze intent
        intent = nlp.analyze_user_intent(user_input)
        print(f"   🎯 Intent: {intent}")
        
        # Handle greetings with Gemini
        if intent['is_greeting']:
            if gemini:
                try:
                    print("   🤖 Generating greeting with Gemini...")
                    greeting = gemini.generate_conversational_response(
                        user_input, 
                        context="User is greeting the LZNK chatbot"
                    )
                    response = {
                        "reply": greeting,
                        "session_id": session_id,
                        "intent": "greeting",
                        "enhanced_by_gemini": True
                    }
                    print(f"   ✅ Gemini greeting: {greeting[:80]}...")
                except Exception as e:
                    print(f"   ⚠️ Gemini error: {e}")
                    response = {
                        "reply": "Assalamualaikum! 👋 Saya ZAKIA dari LZNK. Bagaimana saya boleh membantu anda?",
                        "session_id": session_id,
                        "intent": "greeting"
                    }
            else:
                response = {
                    "reply": "Assalamualaikum! 👋 Saya ZAKIA dari LZNK. Bagaimana saya boleh membantu anda?",
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
                    "reply": "Maaf, sistem sedang mengalami masalah. Sila cuba lagi.",
                    "session_id": session_id
                }), 500
        
        # Get FAQs
        faqs = db.get_faqs()
        if not faqs:
            print("   ❌ No FAQs available")
            # Use Gemini if available
            if gemini:
                try:
                    reply = gemini.generate_conversational_response(user_input)
                    db.log_chat(user_input, reply, session_id)
                    return jsonify({
                        "reply": reply,
                        "session_id": session_id,
                        "enhanced_by_gemini": True,
                        "source": "gemini_only"
                    })
                except:
                    pass
            
            return jsonify({
                "reply": "Maaf, sistem tidak tersedia. Sila hubungi pejabat LZNK.",
                "session_id": session_id
            }), 500
        
        print(f"   📚 Loaded {len(faqs)} FAQs")
        
        # Find best FAQ match
        response_data = nlp.generate_response(
            user_input, 
            faqs, 
            session_id=session_id,
            threshold=0.25  # Lower threshold - we'll use Gemini anyway
        )
        
        confidence = response_data.get('confidence', 0)
        matched_question = response_data.get('matched_question')
        faq_answer = response_data['reply']
        
        print(f"   📊 Confidence: {confidence:.2f}")
        if matched_question:
            print(f"   ✓ Matched FAQ: {matched_question[:60]}...")
        
        # ALWAYS use Gemini if available for better answers
        final_reply = faq_answer
        enhanced_by_gemini = False
        
        if gemini:
            try:
                if confidence >= 0.25 and matched_question:
                    # We have a FAQ match - enhance it with Gemini
                    print(f"   🤖 Enhancing FAQ answer with Gemini...")
                    
                    # Build context
                    context_info = {
                        'matched_question': matched_question,
                        'original_question': user_input,
                        'confidence': confidence
                    }
                    
                    enhanced_reply = gemini.enhance_faq_response(
                        user_input,
                        faq_answer,
                        context=context_info
                    )
                    
                    if enhanced_reply and len(enhanced_reply) >= 20:
                        final_reply = enhanced_reply
                        enhanced_by_gemini = True
                        print(f"   ✅ Gemini enhanced: {final_reply[:80]}...")
                    else:
                        print(f"   ⚠️ Gemini returned invalid response, using FAQ")
                        final_reply = faq_answer
                
                else:
                    # No good FAQ match - use Gemini to generate answer
                    print(f"   🤖 No good FAQ match (confidence: {confidence:.2f})")
                    print(f"   🤖 Generating answer with Gemini...")
                    
                    # Get similar questions for context
                    similar_questions = response_data.get('similar_questions', [])
                    
                    fallback_reply = gemini.generate_fallback_response(
                        user_input,
                        matched_questions=similar_questions
                    )
                    
                    if fallback_reply and len(fallback_reply) >= 20:
                        final_reply = fallback_reply
                        enhanced_by_gemini = True
                        print(f"   ✅ Gemini generated: {final_reply[:80]}...")
                    else:
                        print(f"   ⚠️ Gemini generation failed, using default fallback")
                        final_reply = faq_answer
                
            except Exception as gemini_error:
                print(f"   ❌ Gemini error: {gemini_error}")
                traceback.print_exc()
                final_reply = faq_answer
                enhanced_by_gemini = False
        else:
            print(f"   ℹ️ Gemini not available, using FAQ answer")
        
        # Log chat
        try:
            db.log_chat(user_input, final_reply, session_id)
        except Exception as log_error:
            print(f"   ⚠️ Log error: {log_error}")
        
        # Return response
        return jsonify({
            "reply": final_reply,
            "session_id": session_id,
            "matched_question": matched_question,
            "confidence": round(confidence, 3),
            "confidence_level": response_data.get('confidence_level', 'none'),
            "category": response_data.get('category', 'Umum'),
            "enhanced_by_gemini": enhanced_by_gemini,
            "gemini_available": gemini is not None,
            "intent": intent
        })
        
    except Exception as e:
        print(f"\n❌ CHAT ERROR: {e}")
        traceback.print_exc()
        
        return jsonify({
            "reply": "Maaf, berlaku ralat. Sila cuba lagi.",
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
    """Health check with detailed status"""
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
            "message": "ZAKIA Chatbot operational",
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
                    "mode": "always_on" if gemini else "disabled"
                }
            },
            "version": "3.1 (Always-On Gemini)"
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@chat_bp.route("/test-gemini", methods=["GET"])
def test_gemini():
    """Test Gemini connection"""
    if not gemini:
        return jsonify({
            "success": False,
            "message": "Gemini not initialized",
            "help": "Check GEMINI_API_KEY in .env file"
        }), 503
    
    try:
        print("\n🧪 Testing Gemini API...")
        result = gemini.test_connection()
        print(f"   Result: {result}")
        return jsonify(result)
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": str(e),
            "help": "Verify API key at https://makersuite.google.com/app/apikey"
        }), 500

@chat_bp.route("/debug-chat", methods=["POST"])
def debug_chat():
    """Debug endpoint to see what's happening"""
    try:
        data = request.get_json(silent=True) or {}
        user_input = (data.get("message") or "").strip()
        
        if not user_input:
            return jsonify({"error": "No message provided"})
        
        print(f"\n🔍 DEBUG MODE")
        print(f"   Message: {user_input}")
        
        # Check Gemini
        gemini_working = False
        if gemini:
            try:
                test = gemini.test_connection()
                gemini_working = test.get('success', False)
                print(f"   Gemini: {'✅ Working' if gemini_working else '❌ Failed'}")
            except Exception as e:
                print(f"   Gemini: ❌ Error - {e}")
        else:
            print(f"   Gemini: ❌ Not initialized")
        
        # Check database
        faqs = []
        try:
            if not db.connection or not db.connection.is_connected():
                db.connect()
            faqs = db.get_faqs()
            print(f"   Database: ✅ {len(faqs)} FAQs loaded")
        except Exception as e:
            print(f"   Database: ❌ Error - {e}")
        
        # Check NLP
        print(f"   NLP: {'✅ Trained' if len(nlp.training_pairs) > 0 else '❌ Not trained'}")
        
        # Try to find FAQ match
        if faqs:
            response_data = nlp.generate_response(user_input, faqs, threshold=0.25)
            print(f"   FAQ Match: {response_data.get('confidence', 0):.2f}")
            if response_data.get('matched_question'):
                print(f"   Matched: {response_data['matched_question'][:60]}...")
        
        # Try Gemini directly
        gemini_test = None
        if gemini:
            try:
                gemini_test = gemini.generate_conversational_response(user_input)
                print(f"   Gemini response: {gemini_test[:80]}...")
            except Exception as e:
                print(f"   Gemini direct test: ❌ {e}")
        
        return jsonify({
            "debug": {
                "gemini_initialized": gemini is not None,
                "gemini_working": gemini_working,
                "database_connected": db.connection is not None,
                "faqs_available": len(faqs),
                "nlp_trained": len(nlp.training_pairs) > 0,
                "gemini_test_response": gemini_test[:100] if gemini_test else None
            },
            "user_input": user_input,
            "recommendation": "Check console for detailed logs"
        })
        
    except Exception as e:
        print(f"❌ Debug error: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
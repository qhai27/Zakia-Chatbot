"""
Fixed Admin Routes for ZAKIA Chatbot
Handles FAQ management with proper NLP retraining
"""

from flask import Blueprint, request, jsonify
from database import DatabaseManager
from nlp_processor import NLPProcessor

# Create blueprint
admin_bp = Blueprint('admin', __name__)

# Initialize components
db = DatabaseManager()
nlp = NLPProcessor()

def retrain_nlp_model():
    """Retrain NLP model after FAQ changes"""
    try:
        print("🔄 Retraining NLP model...")
        faqs = db.get_faqs()
        if faqs:
            nlp.train_from_faqs(faqs)
            nlp.save_training_data('training_data.json')
            print("✅ NLP model retrained successfully")
            return True
        return False
    except Exception as e:
        print(f"⚠️ Error retraining NLP: {e}")
        return False

@admin_bp.route("/admin/faqs", methods=["GET"])
def admin_list_faqs():
    """List all FAQs"""
    try:
        # Ensure database connection
        if not db.connection or not db.connection.is_connected():
            print("⚠️ Database not connected, reconnecting...")
            if not db.connect():
                return jsonify({
                    "success": False,
                    "faqs": [], 
                    "error": "Database connection failed"
                }), 500
        
        faqs = db.get_faqs()
        return jsonify({
            "success": True,
            "faqs": faqs,
            "count": len(faqs)
        })
    except Exception as e:
        print(f"❌ Error listing FAQs: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "faqs": [], 
            "error": str(e)
        }), 500

@admin_bp.route("/admin/faqs/<int:faq_id>", methods=["GET"])
def admin_get_faq(faq_id):
    """Get a single FAQ by ID"""
    try:
        # Ensure database connection
        if not db.connection or not db.connection.is_connected():
            if not db.connect():
                return jsonify({
                    "success": False,
                    "error": "Database connection failed"
                }), 500
        
        faq = db.get_faq_by_id(faq_id)
        if not faq:
            return jsonify({
                "success": False,
                "error": "FAQ not found"
            }), 404
        
        return jsonify({
            "success": True,
            "faq": faq
        })
    except Exception as e:
        print(f"❌ Error getting FAQ: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@admin_bp.route("/admin/faqs", methods=["POST"])
def admin_create_faq():
    """Create a new FAQ"""
    try:
        # Ensure database connection
        if not db.connection or not db.connection.is_connected():
            if not db.connect():
                return jsonify({
                    "success": False,
                    "error": "Database connection failed"
                }), 500
        
        # Get data from request
        data = request.get_json(force=True) or {}
        question = (data.get("question") or "").strip()
        answer = (data.get("answer") or "").strip()
        category = (data.get("category") or "Umum").strip()
        
        # Validate input
        if not question:
            return jsonify({
                "success": False,
                "error": "Question is required"
            }), 400
        
        if not answer:
            return jsonify({
                "success": False,
                "error": "Answer is required"
            }), 400
        
        print(f"📝 Creating FAQ: {question[:50]}...")
        
        # Create FAQ
        new_id = db.create_faq(question, answer, category)
        
        if not new_id:
            return jsonify({
                "success": False,
                "error": "Failed to create FAQ"
            }), 500
        
        print(f"✅ FAQ created with ID: {new_id}")
        
        # Retrain NLP model with new FAQ
        retrain_nlp_model()
        
        # Get the created FAQ
        faq = db.get_faq_by_id(new_id)
        
        return jsonify({
            "success": True,
            "faq": faq,
            "message": "FAQ created successfully"
        }), 201
        
    except Exception as e:
        print(f"❌ Error creating FAQ: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@admin_bp.route("/admin/faqs/<int:faq_id>", methods=["PUT", "PATCH"])
def admin_update_faq(faq_id):
    """Update an existing FAQ"""
    try:
        # Ensure database connection
        if not db.connection or not db.connection.is_connected():
            if not db.connect():
                return jsonify({
                    "success": False,
                    "error": "Database connection failed"
                }), 500
        
        # Check if FAQ exists
        existing = db.get_faq_by_id(faq_id)
        if not existing:
            return jsonify({
                "success": False,
                "error": "FAQ not found"
            }), 404
        
        # Get update data
        data = request.get_json(force=True) or {}
        question = (data.get("question") or existing.get("question") or "").strip()
        answer = (data.get("answer") or existing.get("answer") or "").strip()
        category = data.get("category") if "category" in data else existing.get("category")
        
        # Validate
        if not question:
            return jsonify({
                "success": False,
                "error": "Question cannot be empty"
            }), 400
        
        if not answer:
            return jsonify({
                "success": False,
                "error": "Answer cannot be empty"
            }), 400
        
        print(f"✏️ Updating FAQ {faq_id}: {question[:50]}...")
        
        # Update FAQ
        ok = db.update_faq(faq_id, question, answer, category)
        
        if not ok:
            return jsonify({
                "success": False,
                "error": "Failed to update FAQ"
            }), 500
        
        print(f"✅ FAQ {faq_id} updated successfully")
        
        # Retrain NLP model
        retrain_nlp_model()
        
        # Get updated FAQ
        faq = db.get_faq_by_id(faq_id)
        
        return jsonify({
            "success": True,
            "faq": faq,
            "message": "FAQ updated successfully"
        })
        
    except Exception as e:
        print(f"❌ Error updating FAQ: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@admin_bp.route("/admin/faqs/<int:faq_id>", methods=["DELETE"])
def admin_delete_faq(faq_id):
    """Delete an FAQ by ID"""
    try:
        # Ensure database connection
        if not db.connection or not db.connection.is_connected():
            if not db.connect():
                return jsonify({
                    "success": False,
                    "error": "Database connection failed"
                }), 500
        
        # Check if FAQ exists
        existing = db.get_faq_by_id(faq_id)
        if not existing:
            return jsonify({
                "success": False,
                "error": "FAQ not found"
            }), 404
        
        print(f"🗑️ Deleting FAQ {faq_id}...")
        
        # Delete FAQ
        ok = db.delete_faq(faq_id)
        
        if not ok:
            return jsonify({
                "success": False,
                "error": "Failed to delete FAQ"
            }), 500
        
        print(f"✅ FAQ {faq_id} deleted successfully")
        
        # Retrain NLP model
        retrain_nlp_model()
        
        return jsonify({
            "success": True,
            "deleted": True,
            "id": faq_id,
            "message": "FAQ deleted successfully"
        })
        
    except Exception as e:
        print(f"❌ Error deleting FAQ: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@admin_bp.route("/admin/retrain", methods=["POST"])
def admin_retrain_model():
    """Manually retrain the NLP model"""
    try:
        success = retrain_nlp_model()
        
        if success:
            return jsonify({
                "success": True,
                "message": "NLP model retrained successfully",
                "faqs_count": len(db.get_faqs()),
                "keywords_indexed": len(nlp.keyword_index)
            })
        else:
            return jsonify({
                "success": False,
                "error": "No FAQ data available for training"
            }), 400
            
    except Exception as e:
        print(f"❌ Error retraining model: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@admin_bp.route("/admin/stats", methods=["GET"])
def admin_stats():
    """Get admin statistics"""
    try:
        # Ensure database connection
        if not db.connection or not db.connection.is_connected():
            if not db.connect():
                return jsonify({
                    "success": False,
                    "error": "Database connection failed"
                }), 500
        
        faqs = db.get_faqs()
        
        # Count by category
        categories = {}
        for faq in faqs:
            cat = faq.get('category', 'Umum')
            categories[cat] = categories.get(cat, 0) + 1
        
        return jsonify({
            "success": True,
            "stats": {
                "total_faqs": len(faqs),
                "categories": categories,
                "nlp_trained": len(nlp.training_pairs) > 0,
                "keywords_indexed": len(nlp.keyword_index)
            }
        })
        
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
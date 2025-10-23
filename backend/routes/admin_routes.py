"""
Admin routes for ZAKIA Chatbot
Handles FAQ management endpoints
"""

from flask import Blueprint, request, jsonify
from database import DatabaseManager
from nlp_processor import NLPProcessor

# Create blueprint
admin_bp = Blueprint('admin', __name__)

# Initialize components
db = DatabaseManager()
nlp = NLPProcessor()

@admin_bp.route("/admin/faqs", methods=["GET"])
def admin_list_faqs():
    """List all FAQs"""
    try:
        # Ensure database connection
        if not db.connection or not db.connection.is_connected():
            if not db.connect():
                return jsonify({"faqs": [], "error": "Database connection failed"}), 500
        
        faqs = db.get_faqs()
        return jsonify({"faqs": faqs})
    except Exception as e:
        print(f"Error listing FAQs: {e}")
        return jsonify({"faqs": [], "error": str(e)}), 500

@admin_bp.route("/admin/faqs/<int:faq_id>", methods=["GET"])
def admin_get_faq(faq_id):
    """Get a single FAQ by ID"""
    try:
        # Ensure database connection
        if not db.connection or not db.connection.is_connected():
            if not db.connect():
                return jsonify({"error": "Database connection failed"}), 500
        
        faq = db.get_faq_by_id(faq_id)
        if not faq:
            return jsonify({"error": "Not found"}), 404
        return jsonify({"faq": faq})
    except Exception as e:
        print(f"Error getting FAQ: {e}")
        return jsonify({"error": "Server error"}), 500

@admin_bp.route("/admin/faqs", methods=["POST"])
def admin_create_faq():
    """Create a new FAQ"""
    try:
        # Ensure database connection
        if not db.connection or not db.connection.is_connected():
            if not db.connect():
                return jsonify({"error": "Database connection failed"}), 500
        
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

@admin_bp.route("/admin/faqs/<int:faq_id>", methods=["PUT", "PATCH"])
def admin_update_faq(faq_id):
    """Update an existing FAQ"""
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

@admin_bp.route("/admin/faqs/<int:faq_id>", methods=["DELETE"])
def admin_delete_faq(faq_id):
    """Delete an FAQ by ID"""
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

@admin_bp.route("/retrain", methods=["POST"])
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

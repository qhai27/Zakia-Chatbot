"""
Reminder Routes for Zakat Payment System
Handles API endpoints for reminder management
"""

from flask import Blueprint, request, jsonify
from database import DatabaseManager
from reminder_model import ReminderManager
import uuid

# Create blueprint
reminder_bp = Blueprint('reminder', __name__, url_prefix='/api')

# Initialize database and reminder manager
db = DatabaseManager()
if not db.connection or not db.connection.is_connected():
    db.connect()

rm = ReminderManager(db)

@reminder_bp.route('/save-reminder', methods=['POST'])
def save_reminder():
    """
    Save user reminder for zakat payment
    
    Expected JSON payload:
    {
        "name": "Ahmad Bin Ali",
        "ic_number": "950101015678",
        "phone": "0123456789",
        "zakat_type": "pendapatan",
        "zakat_amount": 875.00
    }
    
    Returns:
    {
        "success": true,
        "reply": "Terima kasih Ahmad! Maklumat anda telah direkod...",
        "id": 123
    }
    """
    try:
        payload = request.get_json() or {}
        session_id = payload.get('session_id') or str(uuid.uuid4())
        name = payload.get('name', '').strip()
        ic = payload.get('ic_number', '').strip()
        phone = payload.get('phone', '').strip()
        zakat_type = payload.get('zakat_type', 'umum')
        
        try:
            zakat_amount = float(payload.get('zakat_amount', 0)) if payload.get('zakat_amount') not in (None, '') else 0.0
        except (ValueError, TypeError):
            zakat_amount = 0.0

        print(f"📝 Saving reminder: name={name}, ic={ic}, phone={phone}, type={zakat_type}, amount={zakat_amount}")

        # Validate required fields
        if not name or not ic or not phone:
            return jsonify({
                'success': False, 
                'error': 'Sila lengkapkan nama, nombor IC dan nombor telefon.'
            }), 400

        # Save to database
        res = rm.save(session_id, name, ic, phone, zakat_type, zakat_amount)
        
        if res.get('success'):
            first_name = name.split(' ')[0] if name else 'Pengguna'
            return jsonify({
                'success': True, 
                'id': res.get('id'), 
                'reply': f"✅ Terima kasih {first_name}! Maklumat peringatan anda telah disimpan dengan jayanya. LZNK akan menghantar peringatan zakat kepada anda. 🤲"
            })
        else:
            error_msg = res.get('error', 'Gagal menyimpan maklumat. Sila cuba lagi.')
            print(f"❌ Failed to save reminder: {error_msg}")
            return jsonify({
                'success': False, 
                'error': error_msg
            }), 400
            
    except Exception as e:
        print(f"❌ Error in save_reminder endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'error': 'Ralat sistem. Sila cuba lagi.'
        }), 500

@reminder_bp.route('/reminders', methods=['GET'])
def list_reminders():
    """
    Get all reminders (for admin purposes)
    
    Query params:
    - limit: Number of records to return (default: 50)
    
    Returns:
    {
        "success": true,
        "count": 25,
        "data": [...]
    }
    """
    try:
        limit = int(request.args.get('limit', 50))
        rows = rm.list(limit)
        return jsonify({
            'success': True, 
            'count': len(rows), 
            'data': rows
        })
    except Exception as e:
        print(f"❌ Error in list_reminders: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
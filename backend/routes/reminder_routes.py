"""
Reminder Routes for Zakat Payment System
Handles API endpoints for reminder management
"""

from flask import Blueprint, request, jsonify
from reminder_model import ReminderManager
import uuid

# Create blueprint
reminder_bp = Blueprint('reminder', __name__, url_prefix='/api')

# Initialize components
rm = ReminderManager()

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
        "reminder_id": 123
    }
    """
    payload = request.get_json() or {}
    session_id = payload.get('session_id') or str(uuid.uuid4())
    name = payload.get('name', '').strip()
    ic = payload.get('ic_number', '').strip()
    phone = payload.get('phone', '').strip()
    zakat_type = payload.get('zakat_type')
    try:
        zakat_amount = float(payload.get('zakat_amount')) if payload.get('zakat_amount') not in (None, '') else None
    except Exception:
        zakat_amount = None

    res = rm.save(session_id, name, ic, phone, zakat_type, zakat_amount)
    if res.get('success'):
        return jsonify({'success': True, 'id': res.get('id'), 'reply': f"✅ Terima kasih {name.split(' ')[0]}. Maklumat peringatan telah disimpan."})
    return jsonify({'success': False, 'error': res.get('error', 'Gagal menyimpan')}), 400

@reminder_bp.route('/reminders', methods=['GET'])
def list_reminders():
    """
    Get all reminders (for admin purposes)
    
    Query params:
    - limit: Number of records to return (default: 100)
    
    Returns:
    {
        "success": true,
        "count": 25,
        "reminders": [...]
    }
    """
    limit = int(request.args.get('limit', 50))
    rows = rm.list(limit)
    return jsonify({'success': True, 'count': len(rows), 'data': rows})
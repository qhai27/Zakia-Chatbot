"""
Reminder Routes for Zakat Payment System
Handles API endpoints for reminder management
Saves to user_reminder table
"""

from flask import Blueprint, request, jsonify, current_app
from reminder_model import ReminderManager
import datetime

# Create blueprint
reminder_bp = Blueprint('reminder', __name__)

# Initialize reminder manager (do not auto-create table by default)
rm = ReminderManager(auto_create=False)

@reminder_bp.route('/api/save-reminder', methods=['POST'])
def save_reminder():
    """
    Save user reminder for zakat payment to user_reminder table
    
    Expected JSON payload:
    {
        "name": "Ahmad Bin Ali",
        "ic_number": "950101015678",
        "phone": "0123456789",
        "zakat_type": "pendapatan",  # or "simpanan"
        "zakat_amount": 875.00
    }
    
    Returns:
    {
        "success": true,
        "reply": "Terima kasih Ahmad! Maklumat anda telah direkod...",
        "id": 123
    }
    """
    payload = request.get_json(silent=True) or {}

    # normalize keys
    sanitized = {
        'name': (payload.get('name') or '').strip(),
        'ic_number': (payload.get('ic_number') or payload.get('ic') or '').strip(),
        'phone': (payload.get('phone') or '').strip(),
        'zakat_type': (payload.get('zakat_type') or 'umum').strip(),
        'zakat_amount': payload.get('zakat_amount')
    }

    # Validate quickly before delegating
    if not sanitized['name'] or not sanitized['ic_number'] or not sanitized['phone']:
        return jsonify({'success': False, 'error': 'Sila lengkapkan nama, nombor IC dan nombor telefon.'}), 400

    # Use model.save() — it will attempt to INSERT into "reminders" but will NOT create the table.
    res = rm.save(sanitized)
    if res.get('success'):
        first = (sanitized['name'] or '').split(' ')[0]
        return jsonify({'success': True, 'reply': f"✅ Terima kasih {first}. Maklumat peringatan telah disimpan.", 'id': res.get('id')})
    # save failed (likely table missing) — return error and helpful hint
    err = res.get('error') or 'Gagal menyimpan maklumat.'
    # add hint if it's likely missing table
    if 'no such table' in (err.lower() if isinstance(err, str) else '') or 'doesn\'t exist' in (err.lower() if isinstance(err, str) else ''):
        err += ' (Pastikan jadual "reminders" wujud dalam pangkalan data.)'
    return jsonify({'success': False, 'error': err}), 500
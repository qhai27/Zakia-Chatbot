"""
Reminder Routes for Zakat Payment System
Handles API endpoints for reminder management
"""

from flask import Blueprint, request, jsonify
from reminder_model import ReminderManager
from database import DatabaseManager
import datetime

# Create blueprint - THIS IS THE IMPORTANT PART
reminder_bp = Blueprint('reminder', __name__)

# Initialize database manager
db = DatabaseManager()

@reminder_bp.route('/api/save-reminder', methods=['POST'])
def save_reminder():
    """
    Save user reminder for zakat payment
    
    Expected JSON payload:
    {
        "name": "Ahmad Bin Ali",
        "ic_number": "950101015678",
        "phone": "0123456789",
        "zakat_type": "pendapatan",  # or "simpanan"
        "zakat_amount": 875.00,
        "year": "2025 Masihi"  # Added year field
    }
    
    Returns:
    {
        "success": true,
        "reply": "Terima kasih Ahmad! Maklumat anda telah direkod...",
        "id": 123
    }
    """
    payload = request.get_json(silent=True) or {}

    # Get and normalize all fields
    name = (payload.get('name') or '').strip()
    ic_number = (payload.get('ic_number') or payload.get('ic') or '').strip()
    phone = (payload.get('phone') or '').strip()
    zakat_type = (payload.get('zakat_type') or 'umum').strip()
    year = (payload.get('year') or '').strip()  # Get year field
    
    # Parse zakat amount
    try:
        zakat_amount = float(payload.get('zakat_amount')) if payload.get('zakat_amount') not in (None, '') else None
    except (ValueError, TypeError):
        zakat_amount = None

    # Basic validation
    if not name or not ic_number or not phone:
        return jsonify({
            'success': False, 
            'error': 'Sila lengkapkan nama, nombor IC dan nombor telefon.'
        }), 400

    # Additional validation
    if len(name) < 3:
        return jsonify({
            'success': False,
            'error': 'Nama terlalu pendek.'
        }), 400

    # Clean IC number
    ic_clean = ic_number.replace('-', '').replace(' ', '')
    if not ic_clean.isdigit() or len(ic_clean) != 12:
        return jsonify({
            'success': False,
            'error': 'Nombor IC tidak sah. Sila masukkan 12 digit.'
        }), 400

    try:
        # Ensure database connection
        if not db.connection or not db.connection.is_connected():
            if not db.connect():
                return jsonify({
                    'success': False,
                    'error': 'Ralat sambungan pangkalan data.'
                }), 500

        # Ensure table exists
        ensure_reminders_table()
        
        # Use ReminderManager to save
        rm = ReminderManager(db)
        
        # Prepare data for saving
        reminder_data = {
            'name': name,
            'ic_number': ic_clean,
            'phone': phone,
            'zakat_type': zakat_type,
            'zakat_amount': zakat_amount,
            'year': year
        }
        
        result = rm.save(reminder_data)
        
        if result.get('success'):
            first_name = name.split(' ')[0]
            return jsonify({
                'success': True,
                'reply': f"✅ Terima kasih {first_name}. Maklumat peringatan telah disimpan.",
                'id': result.get('id')
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Gagal menyimpan maklumat.')
            }), 500
            
    except Exception as e:
        print(f"api_save_reminder error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'Gagal menyimpan maklumat. Sila cuba lagi.'
        }), 500


def ensure_reminders_table():
    """Create reminders table if it doesn't exist - with year field"""
    try:
        if not db.connection:
            db.connect()
        conn = db.connection
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                ic_number VARCHAR(32) NOT NULL,
                phone VARCHAR(32) NOT NULL,
                zakat_type VARCHAR(64),
                zakat_amount DECIMAL(12,2),
                year VARCHAR(32),
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        conn.commit()
        cur.close()
        print("✅ Reminders table ensured with year field")
    except Exception as e:
        print(f"ensure_reminders_table error: {e}")


@reminder_bp.route('/api/reminders', methods=['GET'])
def list_reminders():
    """
    List reminders (basic endpoint)
    For admin features, use /admin/reminders instead
    """
    try:
        if not db.connection or not db.connection.is_connected():
            if not db.connect():
                return jsonify({
                    "success": False,
                    "reminders": [],
                    "error": "Database connection failed"
                }), 500
        
        rm = ReminderManager(db)
        reminders = rm.list(limit=10)  # Just return last 10
        
        return jsonify({
            "success": True,
            "reminders": reminders,
            "count": len(reminders)
        })
    except Exception as e:
        print(f"Error listing reminders: {e}")
        return jsonify({
            "success": False,
            "reminders": [],
            "error": str(e)
        }), 500


@reminder_bp.route('/api/reminders/health', methods=['GET'])
def reminder_health():
    """Health check for reminder routes"""
    return jsonify({
        "status": "healthy",
        "message": "Reminder routes operational",
        "endpoints": [
            "POST /api/save-reminder",
            "GET /api/reminders"
        ]
    })
"""
Reminder Routes 

"""

from flask import Blueprint, request, jsonify
from database import DatabaseManager
import datetime
import traceback
import sys

# Create blueprint
reminder_bp = Blueprint('reminder', __name__)

# Initialize database manager
db = DatabaseManager()

def ensure_reminders_table():
    """Create reminders table if it doesn't exist"""
    try:
        print("\n" + "="*60)
        print("🔧 ENSURING REMINDERS TABLE")
        print("="*60)
        
        if not db.connection or not db.connection.is_connected():
            print("📡 Database not connected, connecting...")
            if not db.connect():
                print("❌ Failed to connect to database")
                return False
            print("✅ Connected to database")
        
        conn = db.connection
        cur = conn.cursor()
        
        # Check if table exists
        cur.execute("SHOW TABLES LIKE 'reminders'")
        exists = cur.fetchone() is not None
        
        if exists:
            print("✅ Reminders table already exists")
        else:
            print("📝 Creating reminders table...")
        
        # Create table (won't error if exists due to IF NOT EXISTS)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id_reminder INT AUTO_INCREMENT PRIMARY KEY,
                id_user INT NULL,
                name VARCHAR(255) NOT NULL,
                ic_number VARCHAR(32) NOT NULL,
                phone VARCHAR(32) NOT NULL,
                zakat_type VARCHAR(64),
                zakat_amount DECIMAL(12,2),
                year VARCHAR(32),
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                INDEX idx_ic (ic_number),
                INDEX idx_phone (phone),
                INDEX idx_created (created_at),
                INDEX idx_id_user (id_user),
                FOREIGN KEY (id_user) REFERENCES users(id_user) ON DELETE SET NULL ON UPDATE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        conn.commit()
        cur.close()
        
        print("✅ Reminders table ready")
        print("="*60 + "\n")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR in ensure_reminders_table:")
        print(f"   Type: {type(e).__name__}")
        print(f"   Message: {str(e)}")
        traceback.print_exc()
        return False


@reminder_bp.route('/api/save-reminder', methods=['POST'])
def save_reminder():
    """Save user reminder for zakat payment with enhanced debugging"""
    
    print("\n" + "="*60)
    print("📥 NEW REMINDER REQUEST")
    print("="*60)
    
    try:
        # Step 1: Get payload
        print("\n1️⃣ GETTING PAYLOAD")
        payload = request.get_json(silent=True) or {}
        print(f"   Raw payload type: {type(payload)}")
        print(f"   Raw payload: {payload}")
        
        # Step 2: Check database connection
        print("\n2️⃣ CHECKING DATABASE CONNECTION")
        if not db.connection or not db.connection.is_connected():
            print("   ⚠️ Database not connected, attempting to connect...")
            if not db.connect():
                error_msg = "Failed to connect to database"
                print(f"   ❌ {error_msg}")
                return jsonify({
                    'success': False, 
                    'error': error_msg
                }), 500
        print("   ✅ Database connected")
        
        # Step 3: Ensure table exists
        print("\n3️⃣ ENSURING TABLE EXISTS")
        if not ensure_reminders_table():
            error_msg = "Failed to create/verify reminders table"
            print(f"   ❌ {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg
            }), 500
        
        # Step 4: Extract fields
        print("\n4️⃣ EXTRACTING FIELDS")
        name = (payload.get('name') or '').strip()
        ic_number = (payload.get('ic_number') or payload.get('ic') or '').strip()
        phone = (payload.get('phone') or '').strip()
        zakat_type = (payload.get('zakat_type') or '').strip().lower()
        year = (payload.get('year') or '').strip()
        session_id = payload.get('session_id') or request.headers.get('X-Session-ID')
        
        print(f"   Name: '{name}'")
        print(f"   IC: '{ic_number}'")
        print(f"   Phone: '{phone}'")
        print(f"   Zakat Type: '{zakat_type}'")
        print(f"   Year: '{year}'")
        print(f"   Session ID: '{session_id}'")
        
        # Parse zakat amount
        try:
            zakat_amount = float(payload.get('zakat_amount')) if payload.get('zakat_amount') not in (None, '') else None
            print(f"   Zakat Amount: {zakat_amount}")
        except (ValueError, TypeError) as e:
            print(f"   ⚠️ Error parsing zakat_amount: {e}")
            zakat_amount = None
        
        # Step 5: Validate required fields
        print("\n5️⃣ VALIDATING REQUIRED FIELDS")
        if not name or not ic_number or not phone:
            error_msg = 'Sila lengkapkan nama, nombor IC dan nombor telefon.'
            print(f"   ❌ Validation failed: {error_msg}")
            return jsonify({
                'success': False, 
                'error': error_msg
            }), 400
        print("   ✅ Required fields present")
        
        # Step 6: Validate name length
        print("\n6️⃣ VALIDATING NAME LENGTH")
        if len(name) < 3:
            error_msg = 'Nama terlalu pendek.'
            print(f"   ❌ {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        print(f"   ✅ Name length OK ({len(name)} chars)")
        
        # Step 7: Validate and clean IC
        print("\n7️⃣ VALIDATING IC NUMBER")
        ic_clean = ic_number.replace('-', '').replace(' ', '')
        print(f"   Original: '{ic_number}'")
        print(f"   Cleaned: '{ic_clean}'")
        
        if not ic_clean.isdigit():
            print(f"   ❌ IC contains non-digits")
            return jsonify({
                'success': False,
                'error': 'Nombor IC mesti mengandungi digit sahaja.'
            }), 400
        
        if len(ic_clean) != 12:
            print(f"   ❌ IC length is {len(ic_clean)}, expected 12")
            return jsonify({
                'success': False,
                'error': 'Nombor IC mesti 12 digit.'
            }), 400
        print("   ✅ IC validated")
        
        # Step 8: Clean phone number
        print("\n8️⃣ CLEANING PHONE NUMBER")
        phone_clean = phone.replace('-', '').replace(' ', '')
        print(f"   Original: '{phone}'")
        print(f"   Cleaned: '{phone_clean}'")
        
        if phone_clean.startswith('+60'):
            phone_clean = '0' + phone_clean[3:]
            print(f"   Converted from +60: '{phone_clean}'")
        elif phone_clean.startswith('60') and len(phone_clean) >= 11:
            phone_clean = '0' + phone_clean[2:]
            print(f"   Converted from 60: '{phone_clean}'")
        
        # Step 9: Validate zakat type
        print("\n9️⃣ VALIDATING ZAKAT TYPE")
        if zakat_type and zakat_type not in ['pendapatan', 'simpanan']:
            error_msg = f'Jenis zakat tidak sah: "{zakat_type}". Mesti "pendapatan" atau "simpanan".'
            print(f"   ❌ {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        if not zakat_type:
            zakat_type = 'pendapatan'
            print(f"   ℹ️ Empty zakat_type, defaulting to: '{zakat_type}'")
        else:
            print(f"   ✅ Zakat type valid: '{zakat_type}'")
        
        # Step 9.5: Get user_id from session_id
        print("\n9️⃣.5️⃣ GETTING USER ID FROM SESSION")
        user_id = None
        if session_id:
            user_id = db.get_or_create_user(session_id)
            if user_id:
                print(f"   ✅ Found user_id: {user_id} for session_id: {session_id[:8]}...")
            else:
                print(f"   ⚠️ Could not get/create user for session_id: {session_id[:8]}...")
        else:
            print("   ℹ️ No session_id provided, reminder will not be linked to a user")
        
        # Step 10: Prepare SQL
        print("\n🔟 PREPARING SQL INSERT")
        conn = db.connection
        cur = conn.cursor()
        now = datetime.datetime.utcnow().replace(microsecond=0)
        
        sql = """
            INSERT INTO reminders 
            (id_user, name, ic_number, phone, zakat_type, zakat_amount, year, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            user_id,
            name,
            ic_clean,
            phone_clean,
            zakat_type,
            zakat_amount,
            year,
            now,
            now
        )
        
        print("   SQL:")
        print(f"   {sql}")
        print("   Values:")
        for i, val in enumerate(values, 1):
            print(f"   {i}. {repr(val)} ({type(val).__name__})")
        
        # Step 11: Execute SQL
        print("\n1️⃣1️⃣ EXECUTING SQL")
        cur.execute(sql, values)
        conn.commit()
        insert_id = cur.lastrowid
        cur.close()
        
        print(f"   ✅ INSERT successful!")
        print(f"   📝 New reminder ID: {insert_id}")
        
        # Step 12: Prepare response
        print("\n1️⃣2️⃣ PREPARING RESPONSE")
        first_name = name.split(' ')[0]
        response = {
            'success': True,
            'reply': f"✅ Terima kasih {first_name}. Maklumat peringatan telah disimpan.",
            'id': insert_id
        }
        
        print(f"   Response: {response}")
        print("\n" + "="*60)
        print("✅ REQUEST COMPLETED SUCCESSFULLY")
        print("="*60 + "\n")
        
        return jsonify(response)
        
    except Exception as e:
        print("\n" + "="*60)
        print("❌ CRITICAL ERROR IN save_reminder")
        print("="*60)
        print(f"\nError Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print(f"\nFull Traceback:")
        print("-"*60)
        traceback.print_exc(file=sys.stdout)
        print("-"*60)
        
        # Try to rollback
        try:
            if db.connection:
                db.connection.rollback()
                print("\n🔄 Transaction rolled back")
        except:
            print("\n⚠️ Could not rollback transaction")
        
        print("\n" + "="*60 + "\n")
        
        return jsonify({
            'success': False,
            'error': f'Ralat sistem: {str(e)}'
        }), 500


@reminder_bp.route('/api/reminders/test', methods=['GET'])
def test_connection():
    """Test endpoint to verify everything is working"""
    print("\n🧪 TEST ENDPOINT CALLED")
    
    try:
        # Test database connection
        if not db.connection or not db.connection.is_connected():
            db.connect()
        
        # Test table exists
        cur = db.connection.cursor()
        cur.execute("SHOW TABLES LIKE 'reminders'")
        table_exists = cur.fetchone() is not None
        
        # Get table info if exists
        columns = []
        if table_exists:
            cur.execute("DESCRIBE reminders")
            columns = [{'name': col[0], 'type': col[1]} for col in cur.fetchall()]
        
        cur.close()
        
        return jsonify({
            'status': 'ok',
            'database_connected': True,
            'table_exists': table_exists,
            'columns': columns
        })
        
    except Exception as e:
        print(f"❌ Test endpoint error: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@reminder_bp.route('/api/reminders', methods=['GET'])
def list_reminders():
    """List reminders"""
    try:
        if not db.connection or not db.connection.is_connected():
            if not db.connect():
                return jsonify({
                    "success": False,
                    "reminders": [],
                    "error": "Database connection failed"
                }), 500
        
        cur = db.connection.cursor(dictionary=True)
        cur.execute("SELECT * FROM reminders ORDER BY created_at DESC LIMIT 10")
        reminders = cur.fetchall()
        cur.close()
        
        return jsonify({
            "success": True,
            "reminders": reminders,
            "count": len(reminders)
        })
    except Exception as e:
        print(f"Error listing reminders: {e}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "reminders": [],
            "error": str(e)
        }), 500


@reminder_bp.route('/api/reminders/health', methods=['GET'])
def reminder_health():
    """Health check for reminder routes"""
    try:
        # Check database connection
        if not db.connection or not db.connection.is_connected():
            db.connect()
        
        # Check if table exists
        cur = db.connection.cursor()
        cur.execute("SHOW TABLES LIKE 'reminders'")
        table_exists = cur.fetchone() is not None
        cur.close()
        
        return jsonify({
            "status": "healthy",
            "message": "Reminder routes operational",
            "database_connected": db.connection.is_connected() if db.connection else False,
            "table_exists": table_exists,
            "endpoints": [
                "POST /api/save-reminder",
                "GET /api/reminders",
                "GET /api/reminders/test",
                "GET /api/reminders/health"
            ]
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500
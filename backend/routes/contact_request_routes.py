"""
Contact Request Routes - Replaces Live Chat Escalation
Handles user contact requests for human assistance
"""

from flask import Blueprint, request, jsonify
from database import DatabaseManager
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo  # Python 3.9+
import logging
import json

contact_bp = Blueprint('contact', __name__, url_prefix='/contact-request')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Shared DB manager
db = DatabaseManager()


def ensure_connection(local_db):
    """Ensure database connection is active"""
    try:
        if not local_db.connection or not local_db.connection.is_connected():
            logger.info("🔄 Reconnecting to database...")
            return local_db.connect()
        return True
    except Exception as e:
        logger.error(f"❌ Connection error: {e}")
        return False


def check_office_hours():
    """
    Check if current time is within LZNK office hours
    
    Office Hours:
    - Sunday-Wednesday: 9am - 5pm
    - Thursday: 9am - 3:30pm
    - Friday-Saturday: Closed
    
    Returns:
        bool: True if within office hours, False otherwise
    """
    try:
        # Use ZoneInfo (Python 3.9+) or fallback to UTC offset
        try:
            kl_tz = ZoneInfo('Asia/Kuala_Lumpur')
            now = datetime.now(kl_tz)
        except:
            # Fallback: UTC+8 (Malaysia timezone)
            from datetime import timezone
            kl_offset = timezone(timedelta(hours=8))
            now = datetime.now(kl_offset)
        
        weekday = now.weekday()  # 0=Monday, 6=Sunday
        hour = now.hour
        minute = now.minute
        
        # Convert to Sunday=0 format
        day = (weekday + 1) % 7
        
        logger.info(f"⏰ Checking office hours: Day={day} (0=Sun), Hour={hour}:{minute:02d}")
        
        # Friday (5) or Saturday (6) - closed
        if day in [5, 6]:
            logger.info("   ❌ Outside hours: Weekend (Friday/Saturday)")
            return False
        
        # Thursday (4) - until 3:30pm
        if day == 4:
            is_open = (hour >= 9) and (hour < 15 or (hour == 15 and minute <= 30))
            logger.info(f"   {'✅' if is_open else '❌'} Thursday hours: {hour}:{minute:02d}")
            return is_open
        
        # Sunday-Wednesday - 9am to 5pm
        if day in [0, 1, 2, 3]:
            is_open = hour >= 9 and hour < 17
            logger.info(f"   {'✅' if is_open else '❌'} Weekday hours: {hour}:{minute:02d}")
            return is_open
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Office hours check error: {e}")
        return False  # Default to closed on error


def get_next_working_day():
    """
    Calculate the next working day
    
    Returns:
        str: Formatted date of next working day
    """
    try:
        # Use ZoneInfo or fallback
        try:
            kl_tz = ZoneInfo('Asia/Kuala_Lumpur')
            now = datetime.now(kl_tz)
        except:
            from datetime import timezone
            kl_offset = timezone(timedelta(hours=8))
            now = datetime.now(kl_offset)
        
        current_day = (now.weekday() + 1) % 7  # 0=Sunday
        
        # Map to next working day
        if current_day == 4:  # Thursday after 3:30pm
            days_to_add = 3  # Go to Sunday
        elif current_day == 5:  # Friday
            days_to_add = 2  # Go to Sunday
        elif current_day == 6:  # Saturday
            days_to_add = 1  # Go to Sunday
        else:
            days_to_add = 1  # Next day
        
        next_day = now + timedelta(days=days_to_add)
        
        # Format: "Ahad, 15 Januari 2025"
        day_names_ms = ['Ahad', 'Isnin', 'Selasa', 'Rabu', 'Khamis', 'Jumaat', 'Sabtu']
        month_names_ms = ['Januari', 'Februari', 'Mac', 'April', 'Mei', 'Jun',
                         'Julai', 'Ogos', 'September', 'Oktober', 'November', 'Disember']
        
        day_name = day_names_ms[(next_day.weekday() + 1) % 7]
        month_name = month_names_ms[next_day.month - 1]
        
        return f"{day_name}, {next_day.day} {month_name} {next_day.year}"
        
    except Exception as e:
        logger.error(f"❌ Error calculating next working day: {e}")
        return "hari bekerja berikutnya"


@contact_bp.route('', methods=['POST'])
def submit_contact_request():
    """
    Submit a contact request form
    
    Expected JSON payload:
    {
        "session_id": "abc123",
        "name": "Ahmad bin Ali",
        "phone": "+60123456789",
        "email": "ahmad@email.com",  // optional
        "question": "Saya nak tanya tentang...",
        "preferred_method": "whatsapp",  // whatsapp|phone|email
        "conversation_history": [...],  // Last 5 messages
        "trigger_type": "confusion"  // explicit_request|confusion|repetition|complexity
    }
    
    Returns:
        JSON with success status, request_id, and appropriate message
    """
    try:
        payload = request.get_json(silent=True) or {}
        
        # Extract and validate fields
        session_id = (payload.get('session_id') or '').strip() or None
        name = (payload.get('name') or '').strip()
        phone = (payload.get('phone') or '').strip()
        email = (payload.get('email') or '').strip() or None
        question = (payload.get('question') or '').strip()
        preferred_method = payload.get('preferred_method', 'whatsapp')
        conversation_history = payload.get('conversation_history', [])
        trigger_type = payload.get('trigger_type')
        
        logger.info(f"\n📝 NEW CONTACT REQUEST")
        logger.info(f"   Name: {name}")
        logger.info(f"   Phone: {phone}")
        logger.info(f"   Email: {email}")
        logger.info(f"   Method: {preferred_method}")
        logger.info(f"   Trigger: {trigger_type}")
        
        # Validation
        if not name:
            return jsonify({
                "success": False,
                "error": "Nama diperlukan"
            }), 400
        
        if not phone:
            return jsonify({
                "success": False,
                "error": "Nombor telefon diperlukan"
            }), 400
        
        if not question:
            return jsonify({
                "success": False,
                "error": "Soalan diperlukan"
            }), 400
        
        # Validate preferred method
        valid_methods = ['whatsapp', 'phone', 'email']
        if preferred_method not in valid_methods:
            preferred_method = 'whatsapp'
        
        # Connect to database
        if not ensure_connection(db):
            logger.error("❌ Database connection failed")
            return jsonify({
                "success": False,
                "error": "Gagal menyambung ke pangkalan data"
            }), 500
        
        cursor = db.connection.cursor()
        
        try:
            # Convert conversation history to JSON string
            history_json = json.dumps(conversation_history) if conversation_history else None
            
            # Insert request
            cursor.execute("""
                INSERT INTO contact_requests 
                (session_id, name, phone, email, question, preferred_contact_method,
                 conversation_history, trigger_type, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending', CURRENT_TIMESTAMP)
            """, (
                session_id, name, phone, email, question, preferred_method,
                history_json, trigger_type
            ))
            
            db.connection.commit()
            request_id = cursor.lastrowid
            
            logger.info(f"✅ Contact request created: ID={request_id}")
            
            # Check office hours
            is_office_hours = check_office_hours()
            
            # Prepare response message
            if is_office_hours:
                message = "Terima kasih! Pegawai kami akan menghubungi anda dalam masa 2-4 jam bekerja."
                estimated_response = "2-4 jam bekerja"
            else:
                next_day = get_next_working_day()
                message = f"Terima kasih! Permintaan anda telah diterima. Pegawai kami akan menghubungi anda pada {next_day}."
                estimated_response = next_day
            
            # TODO: Send notification to admin
            # - Email notification
            # - Slack/Discord webhook
            # - WhatsApp Business API notification
            
            logger.info(f"   Office Hours: {'✅ Yes' if is_office_hours else '❌ No'}")
            logger.info(f"   Response ETA: {estimated_response}")
            
            return jsonify({
                "success": True,
                "request_id": request_id,
                "is_office_hours": is_office_hours,
                "estimated_response": estimated_response,
                "message": message
            })
            
        except Exception as e:
            logger.error(f"❌ Database insert error: {e}")
            db.connection.rollback()
            return jsonify({
                "success": False,
                "error": "Gagal menyimpan permintaan"
            }), 500
            
        finally:
            cursor.close()
        
    except Exception as e:
        logger.error(f"❌ Contact request error: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "success": False,
            "error": "Ralat sistem. Sila cuba lagi."
        }), 500


@contact_bp.route('/status/<session_id>', methods=['GET'])
def check_status(session_id):
    """
    Check status of contact requests for a session
    
    Returns:
        JSON with list of requests for this session
    """
    try:
        if not ensure_connection(db):
            return jsonify({
                "success": False,
                "error": "Database connection failed"
            }), 500
        
        cursor = db.connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                id, name, phone, question, status,
                preferred_contact_method, created_at, contacted_at
            FROM contact_requests
            WHERE session_id = %s
            ORDER BY created_at DESC
            LIMIT 10
        """, (session_id,))
        
        rows = cursor.fetchall()
        cursor.close()
        
        # Format datetime objects
        for row in rows:
            if row.get('created_at'):
                row['created_at'] = row['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if row.get('contacted_at'):
                row['contacted_at'] = row['contacted_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            "success": True,
            "requests": rows,
            "count": len(rows)
        })
        
    except Exception as e:
        logger.error(f"❌ Status check error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@contact_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        db_connected = ensure_connection(db)
        is_office_hours = check_office_hours()
        
        return jsonify({
            "success": True,
            "service": "contact_request",
            "status": "operational",
            "database": "connected" if db_connected else "disconnected",
            "office_hours": "open" if is_office_hours else "closed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
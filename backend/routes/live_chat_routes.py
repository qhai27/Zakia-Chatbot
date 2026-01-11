"""
Live Chat Escalation Routes
Allows users to escalate when bot answers are not satisfactory.
"""

from flask import Blueprint, request, jsonify
from database import DatabaseManager
import logging

live_chat_bp = Blueprint('live_chat', __name__, url_prefix='/live-chat')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Shared DB manager
db = DatabaseManager()


def ensure_connection(local_db):
    """Ensure database connection is active"""
    if not local_db.connection or not local_db.connection.is_connected():
        if not local_db.connect():
            return False
    
    # CRITICAL FIX: Set transaction isolation level to READ COMMITTED
    # This ensures we see commits from other connections immediately
    # MySQL default is REPEATABLE READ which can cause stale reads
    try:
        cursor_temp = local_db.connection.cursor()
        cursor_temp.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
        cursor_temp.close()
        logger.debug("   ✅ Set isolation level to READ COMMITTED")
    except Exception as e:
        logger.warning(f"   ⚠️ Could not set isolation level: {e}")
    
    return True


@live_chat_bp.route('/request', methods=['POST'])
def create_live_chat_request():
    """Create a new live chat escalation request."""
    try:
        payload = request.get_json(silent=True) or {}
        session_id = (payload.get('session_id') or '').strip() or None
        user_message = (payload.get('user_message') or '').strip()
        bot_response = (payload.get('bot_response') or '').strip()

        if not user_message:
            return jsonify({"success": False, "error": "user_message is required"}), 400

        if not session_id:
            logger.warning("Live chat request without session_id")
            return jsonify({"success": False, "error": "session_id is required"}), 400

        if not ensure_connection(db):
            logger.error("DB connection failed")
            return jsonify({"success": False, "error": "DB connection failed"}), 500

        cursor = db.connection.cursor()
        
        # Insert new live chat request
        cursor.execute("""
            INSERT INTO live_chat_requests 
            (session_id, user_message, bot_response, status, is_delivered, created_at)
            VALUES (%s, %s, %s, 'open', 0, CURRENT_TIMESTAMP)
        """, (session_id, user_message, bot_response))
        
        db.connection.commit()
        request_id = cursor.lastrowid
        cursor.close()

        logger.info(f"✅ Live chat request created: ID={request_id}, Session={session_id[:8]}")

        return jsonify({
            "success": True,
            "id": request_id,
            "status": "open",
            "message": "Request sent to admin"
        })
        
    except Exception as e:
        logger.error(f"❌ Live chat request error: {e}")
        if db.connection:
            db.connection.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@live_chat_bp.route('/pending', methods=['GET'])
def get_pending_response():
    """
    Get the latest resolved admin response for a session that hasn't been delivered yet.
    Marks it as delivered after retrieval.
    """
    try:
        session_id = (request.args.get('session_id') or '').strip()
        
        if not session_id:
            return jsonify({
                "success": False, 
                "error": "session_id is required"
            }), 400

        logger.info(f"\n🔍 CHECKING FOR ADMIN RESPONSE")
        logger.info(f"   Session ID: {session_id[:16]}...")

        if not ensure_connection(db):
            logger.error("   ❌ DB connection failed")
            return jsonify({
                "success": False, 
                "error": "DB connection failed"
            }), 500

        # CRITICAL FIX: Get a fresh connection to ensure we see the latest committed data
        # The admin route uses a different connection, so we need to ensure we see its commits
        try:
            # Close existing connection to force a new one from the pool
            if db.connection and db.connection.is_connected():
                db.connection.close()
                logger.info("   🔄 Closed existing connection to get fresh one")
            
            # Get a new connection that will see the latest commits
            if not db.connect():
                logger.error("   ❌ Failed to get fresh connection")
                return jsonify({
                    "success": False,
                    "error": "Failed to get fresh database connection"
                }), 500
        except Exception as e:
            logger.warning(f"   ⚠️ Could not refresh connection: {e}, using existing")

        cursor = db.connection.cursor(dictionary=True)
        
        # Find undelivered resolved responses - ONLY for this session_id
        query = """
            SELECT 
                id, 
                session_id,
                admin_response, 
                admin_name, 
                user_message, 
                bot_response, 
                updated_at,
                created_at,
                status,
                is_delivered
            FROM live_chat_requests
            WHERE session_id = %s
              AND status = 'resolved'
              AND is_delivered = 0
              AND admin_response IS NOT NULL
              AND admin_response != ''
            ORDER BY updated_at DESC
            LIMIT 1
        """
        
        logger.info(f"   🔎 Executing query for session_id: {session_id[:16]}...")
        
        # Debug: Check what records exist for this session_id
        debug_query = """
            SELECT id, status, is_delivered, 
                   CASE WHEN admin_response IS NULL THEN 'NULL' 
                        WHEN admin_response = '' THEN 'EMPTY' 
                        ELSE 'HAS_VALUE' END as admin_response_status,
                   LENGTH(admin_response) as response_length,
                   updated_at
            FROM live_chat_requests
            WHERE session_id = %s
            ORDER BY updated_at DESC
            LIMIT 5
        """
        cursor.execute(debug_query, (session_id,))
        debug_rows = cursor.fetchall()
        logger.info(f"   🔍 DEBUG: Found {len(debug_rows)} records for this session_id:")
        for dr in debug_rows:
            logger.info(f"      ID: {dr['id']}, Status: {dr['status']}, IsDelivered: {dr['is_delivered']}, "
                       f"AdminResponse: {dr['admin_response_status']}, Length: {dr['response_length']}, "
                       f"Updated: {dr['updated_at']}")
        
        cursor.execute(query, (session_id,))
        
        row = cursor.fetchone()

        if not row:
            cursor.close()
            logger.info(f"   ⏳ No pending response found for session_id: {session_id[:16]}")
            logger.info(f"   💡 Query criteria: status='resolved', is_delivered=0, admin_response IS NOT NULL AND != ''")
            return jsonify({
                "success": True, 
                "pending": False,
                "message": "No pending admin response"
            })
        
        # Verify session_id matches (safety check)
        if row.get('session_id') != session_id:
            cursor.close()
            logger.error(f"   ❌ Session ID mismatch! Expected: {session_id[:16]}, Got: {row.get('session_id', 'None')[:16] if row.get('session_id') else 'None'}")
            return jsonify({
                "success": False,
                "error": "Session ID mismatch"
            }), 500

        # Mark as delivered
        logger.info(f"   📨 ADMIN RESPONSE FOUND!")
        logger.info(f"      Request ID: {row['id']}")
        logger.info(f"      Admin: {row['admin_name']}")
        logger.info(f"      Response: {row['admin_response'][:50]}...")
        logger.info(f"      Status: {row['status']}")
        logger.info(f"      Is Delivered: {row['is_delivered']}")
        
        cursor.execute("""
            UPDATE live_chat_requests
            SET is_delivered = 1, 
                delivered_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (row['id'],))
        
        db.connection.commit()
        logger.info(f"   ✅ Marked as delivered")
        
        cursor.close()

        response_data = {
            "success": True,
            "pending": True,
            "response": {
                "id": row['id'],
                "admin_response": row['admin_response'],
                "admin_name": row['admin_name'] or 'Admin',
                "user_message": row['user_message'],
                "bot_response": row['bot_response'],
                "updated_at": row['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if row['updated_at'] else None,
                "created_at": row['created_at'].strftime('%Y-%m-%d %H:%M:%S') if row['created_at'] else None
            }
        }
        
        logger.info(f"   📤 Sending response to user")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"❌ Live chat pending error: {e}")
        import traceback
        traceback.print_exc()
        if db.connection:
            db.connection.rollback()
        return jsonify({
            "success": False, 
            "error": str(e)
        }), 500


@live_chat_bp.route('/status/<session_id>', methods=['GET'])
def check_status(session_id):
    """
    Check if there are any open or resolved requests for a session.
    """
    try:
        if not ensure_connection(db):
            return jsonify({
                "success": False, 
                "error": "DB connection failed"
            }), 500

        cursor = db.connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                id, 
                status, 
                admin_response,
                is_delivered,
                created_at,
                updated_at
            FROM live_chat_requests
            WHERE session_id = %s
            ORDER BY created_at DESC
            LIMIT 5
        """, (session_id,))
        
        rows = cursor.fetchall()
        cursor.close()

        if not rows:
            return jsonify({
                "success": True,
                "has_request": False
            })

        return jsonify({
            "success": True,
            "has_request": True,
            "requests": [
                {
                    "id": row['id'],
                    "status": row['status'],
                    "has_response": bool(row['admin_response']),
                    "is_delivered": bool(row['is_delivered']),
                    "created_at": row['created_at'].strftime('%Y-%m-%d %H:%M:%S') if row['created_at'] else None,
                    "updated_at": row['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if row['updated_at'] else None
                }
                for row in rows
            ]
        })
        
    except Exception as e:
        logger.error(f"❌ Status check error: {e}")
        return jsonify({
            "success": False, 
            "error": str(e)
        }), 500


@live_chat_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        db_connected = ensure_connection(db)
        return jsonify({
            "success": True,
            "service": "live_chat",
            "status": "operational",
            "database": "connected" if db_connected else "disconnected"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
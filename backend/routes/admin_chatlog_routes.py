"""
Fixed Admin Chat Log Routes with Delete & Real-time Support
Handles chat log management with proper timezone handling
"""

from flask import Blueprint, request, jsonify
from database import DatabaseManager
from datetime import datetime
import pytz

# Create blueprint
admin_chatlog_bp = Blueprint('admin_chatlog', __name__, url_prefix='/admin/chat-logs')

# Initialize database
db = DatabaseManager()

# Timezone for Malaysia
MALAYSIA_TZ = pytz.timezone('Asia/Kuala_Lumpur')

def format_timestamp(dt):
    """Format timestamp to Malaysia timezone"""
    if dt is None:
        return None
    
    # If datetime is naive (no timezone), assume it's UTC
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    
    # Convert to Malaysia timezone
    malaysia_time = dt.astimezone(MALAYSIA_TZ)
    return malaysia_time.strftime('%Y-%m-%d %H:%M:%S')

@admin_chatlog_bp.route('', methods=['GET'])
def list_chat_logs():
    """
    List all chat logs with pagination
    Query params:
    - limit: number of records (default: 100)
    - offset: starting position (default: 0)
    - search: search term for messages, session_id, or user_id
    
    Returns:
    {
        "success": true,
        "logs": [...],
        "count": 10,
        "total": 150
    }
    """
    try:
        # Parse query parameters
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        search = request.args.get('search', '').strip()
        
        # Ensure database connection
        if not db.connection or not db.connection.is_connected():
            print("⚠️ Database not connected, attempting to connect...")
            if not db.connect():
                print("❌ Database connection failed")
                return jsonify({
                    "success": False,
                    "logs": [],
                    "count": 0,
                    "total": 0,
                    "error": "Database connection failed"
                }), 500
            print("✅ Database connected successfully")
        
        cursor = db.connection.cursor(dictionary=True)
        
        # Build WHERE clause for search
        where_clause = ""
        params = []
        
        if search:
            where_clause = """
                WHERE user_message LIKE %s 
                OR bot_response LIKE %s 
                OR session_id LIKE %s
                OR CAST(id_user AS CHAR) LIKE %s
            """
            search_param = f"%{search}%"
            params = [search_param, search_param, search_param, search_param]
        
        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM chat_logs {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        # Get paginated results
        query = f"""
            SELECT 
                id_log,
                id_user,
                session_id,
                user_message,
                bot_response,
                created_at
            FROM chat_logs
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        
        cursor.execute(query, params + [limit, offset])
        rows = cursor.fetchall()
        
        # Format timestamps
        logs = []
        for row in rows:
            log = dict(row)
            if log.get('created_at'):
                log['created_at'] = format_timestamp(log['created_at'])
            logs.append(log)
        
        cursor.close()
        
        print(f"✅ Successfully fetched {len(logs)} chat logs (total: {total})")
        
        return jsonify({
            "success": True,
            "logs": logs,
            "count": len(logs),
            "total": total
        })
        
    except ValueError as e:
        print(f"❌ Invalid parameter: {e}")
        return jsonify({
            "success": False,
            "logs": [],
            "count": 0,
            "total": 0,
            "error": f"Invalid parameter: {str(e)}"
        }), 400
        
    except Exception as e:
        print(f"❌ Error listing chat logs: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "logs": [],
            "count": 0,
            "total": 0,
            "error": str(e)
        }), 500

@admin_chatlog_bp.route('/<int:log_id>', methods=['GET'])
def get_chat_log(log_id):
    """
    Get single chat log by ID
    
    Args:
        log_id: The ID of the chat log
    
    Returns:
    {
        "success": true,
        "log": {...}
    }
    """
    try:
        # Ensure database connection
        if not db.connection or not db.connection.is_connected():
            if not db.connect():
                return jsonify({
                    "success": False,
                    "error": "Database connection failed"
                }), 500
        
        cursor = db.connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                id_log,
                id_user,
                session_id,
                user_message,
                bot_response,
                created_at
            FROM chat_logs
            WHERE id_log = %s
        """, (log_id,))
        
        row = cursor.fetchone()
        cursor.close()
        
        if not row:
            return jsonify({
                "success": False,
                "error": "Chat log not found"
            }), 404
        
        log = dict(row)
        if log.get('created_at'):
            log['created_at'] = format_timestamp(log['created_at'])
        
        return jsonify({
            "success": True,
            "log": log
        })
        
    except Exception as e:
        print(f"❌ Error getting chat log {log_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@admin_chatlog_bp.route('/<int:log_id>', methods=['DELETE'])
def delete_chat_log(log_id):
    """
    Delete a chat log by ID
    
    Args:
        log_id: The ID of the chat log to delete
    
    Returns:
    {
        "success": true,
        "deleted": true,
        "id": 123
    }
    """
    try:
        # Ensure database connection
        if not db.connection or not db.connection.is_connected():
            if not db.connect():
                return jsonify({
                    "success": False,
                    "error": "Database connection failed"
                }), 500
        
        cursor = db.connection.cursor()
        
        # Check if log exists
        cursor.execute("SELECT id_log FROM chat_logs WHERE id_log = %s", (log_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({
                "success": False,
                "error": "Chat log not found"
            }), 404
        
        # Delete the log
        cursor.execute("DELETE FROM chat_logs WHERE id_log = %s", (log_id,))
        db.connection.commit()
        cursor.close()
        
        print(f"✅ Successfully deleted chat log {log_id}")
        
        return jsonify({
            "success": True,
            "deleted": True,
            "id": log_id
        })
        
    except Exception as e:
        print(f"❌ Error deleting chat log {log_id}: {e}")
        import traceback
        traceback.print_exc()
        
        # Rollback on error
        if db.connection:
            db.connection.rollback()
        
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@admin_chatlog_bp.route('/bulk-delete', methods=['POST'])
def bulk_delete_chat_logs():
    """
    Delete multiple chat logs
    
    Request body:
    {
        "ids": [1, 2, 3, 4, 5]
    }
    
    Returns:
    {
        "success": true,
        "deleted_count": 5,
        "failed": []
    }
    """
    try:
        data = request.get_json() or {}
        ids = data.get('ids', [])
        
        if not ids or not isinstance(ids, list):
            return jsonify({
                "success": False,
                "error": "Invalid or empty 'ids' array"
            }), 400
        
        # Ensure database connection
        if not db.connection or not db.connection.is_connected():
            if not db.connect():
                return jsonify({
                    "success": False,
                    "error": "Database connection failed"
                }), 500
        
        cursor = db.connection.cursor()
        
        deleted_count = 0
        failed = []
        
        for log_id in ids:
            try:
                cursor.execute("DELETE FROM chat_logs WHERE id_log = %s", (log_id,))
                if cursor.rowcount > 0:
                    deleted_count += 1
                else:
                    failed.append({"id": log_id, "reason": "Not found"})
            except Exception as e:
                failed.append({"id": log_id, "reason": str(e)})
        
        db.connection.commit()
        cursor.close()
        
        print(f"✅ Bulk delete completed: {deleted_count} deleted, {len(failed)} failed")
        
        return jsonify({
            "success": True,
            "deleted_count": deleted_count,
            "failed": failed
        })
        
    except Exception as e:
        print(f"❌ Error in bulk delete: {e}")
        import traceback
        traceback.print_exc()
        
        # Rollback on error
        if db.connection:
            db.connection.rollback()
        
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@admin_chatlog_bp.route('/stats', methods=['GET'])
def get_chat_stats():
    """
    Get chat log statistics
    
    Returns:
    {
        "success": true,
        "stats": {
            "total_logs": 150,
            "total_users": 45,
            "total_sessions": 60,
            "today_logs": 12,
            "this_week_logs": 45,
            "this_month_logs": 120
        }
    }
    """
    try:
        # Ensure database connection
        if not db.connection or not db.connection.is_connected():
            if not db.connect():
                return jsonify({
                    "success": False,
                    "error": "Database connection failed"
                }), 500
        
        cursor = db.connection.cursor(dictionary=True)
        
        # Total logs
        cursor.execute("SELECT COUNT(*) as total FROM chat_logs")
        total_logs = cursor.fetchone()['total']
        
        # Unique users
        cursor.execute("SELECT COUNT(DISTINCT id_user) as total FROM chat_logs WHERE id_user IS NOT NULL")
        total_users = cursor.fetchone()['total']
        
        # Unique sessions
        cursor.execute("SELECT COUNT(DISTINCT session_id) as total FROM chat_logs")
        total_sessions = cursor.fetchone()['total']
        
        # Today's logs
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM chat_logs 
            WHERE DATE(created_at) = CURDATE()
        """)
        today_logs = cursor.fetchone()['total']
        
        # This week's logs
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM chat_logs 
            WHERE YEARWEEK(created_at, 1) = YEARWEEK(CURDATE(), 1)
        """)
        this_week_logs = cursor.fetchone()['total']
        
        # This month's logs
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM chat_logs 
            WHERE YEAR(created_at) = YEAR(CURDATE()) 
            AND MONTH(created_at) = MONTH(CURDATE())
        """)
        this_month_logs = cursor.fetchone()['total']
        
        cursor.close()
        
        stats = {
            "total_logs": total_logs,
            "total_users": total_users,
            "total_sessions": total_sessions,
            "today_logs": today_logs,
            "this_week_logs": this_week_logs,
            "this_month_logs": this_month_logs
        }
        
        return jsonify({
            "success": True,
            "stats": stats
        })
        
    except Exception as e:
        print(f"❌ Error getting chat stats: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@admin_chatlog_bp.route('/clear-old', methods=['POST'])
def clear_old_logs():
    """
    Clear chat logs older than specified days
    
    Request body:
    {
        "days": 30
    }
    
    Returns:
    {
        "success": true,
        "deleted_count": 50
    }
    """
    try:
        data = request.get_json() or {}
        days = int(data.get('days', 30))
        
        if days < 1:
            return jsonify({
                "success": False,
                "error": "Days must be at least 1"
            }), 400
        
        # Ensure database connection
        if not db.connection or not db.connection.is_connected():
            if not db.connect():
                return jsonify({
                    "success": False,
                    "error": "Database connection failed"
                }), 500
        
        cursor = db.connection.cursor()
        
        # Delete old logs
        cursor.execute("""
            DELETE FROM chat_logs 
            WHERE created_at < DATE_SUB(NOW(), INTERVAL %s DAY)
        """, (days,))
        
        deleted_count = cursor.rowcount
        db.connection.commit()
        cursor.close()
        
        print(f"✅ Cleared {deleted_count} logs older than {days} days")
        
        return jsonify({
            "success": True,
            "deleted_count": deleted_count
        })
        
    except Exception as e:
        print(f"❌ Error clearing old logs: {e}")
        import traceback
        traceback.print_exc()
        
        # Rollback on error
        if db.connection:
            db.connection.rollback()
        
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Health check endpoint
@admin_chatlog_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for chat log routes"""
    try:
        # Test database connection
        if not db.connection or not db.connection.is_connected():
            db.connect()
        
        cursor = db.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM chat_logs")
        count = cursor.fetchone()[0]
        cursor.close()
        
        return jsonify({
            "status": "healthy",
            "message": "Chat log routes operational",
            "database_connected": db.connection.is_connected() if db.connection else False,
            "total_logs": count
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500
"""
Admin Chat Log Routes
This blueprint serves endpoints used by the admin panel to list, delete,
bulk‑delete and obtain statistics about chat logs.
"""

from flask import Blueprint, request, jsonify, make_response
from database import DatabaseManager

admin_chatlog_bp = Blueprint('admin_chatlog', __name__, url_prefix='/admin/chat-logs')
db = DatabaseManager()

# OPTIONS handler to satisfy preflight checks
@admin_chatlog_bp.route('', methods=['OPTIONS'])
def chatlogs_options():
    resp = make_response('', 200)
    return resp


# ---------- actual chat log endpoints ----------
@admin_chatlog_bp.route('', methods=['GET'])
def list_chat_logs():
    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        search = request.args.get('search', '').strip()

        if not db.connection or not db.connection.is_connected():
            db.connect()

        cursor = db.connection.cursor(dictionary=True)
        where_clause = ""
        params = []
        if search:
            where_clause = (
                " WHERE user_message LIKE %s "
                " OR bot_response LIKE %s "
                " OR session_id LIKE %s "
                " OR CAST(id_user AS CHAR) LIKE %s "
            )
            sp = f"%{search}%"
            params = [sp, sp, sp, sp]

        cursor.execute(f"SELECT COUNT(*) as total FROM chat_logs{where_clause}", params)
        total = cursor.fetchone()['total']

        query = (
            "SELECT id_log, id_user, session_id, user_message, bot_response, created_at "
            "FROM chat_logs" + where_clause + " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        )
        cursor.execute(query, params + [limit, offset])
        rows = cursor.fetchall()
        logs = []
        for r in rows:
            log = dict(r)
            if log.get('created_at'):
                log['created_at'] = log['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            logs.append(log)
        cursor.close()
        return jsonify({"success": True, "logs": logs, "count": len(logs), "total": total})
    except Exception as e:
        print(f"❌ Error listing chat logs: {e}")
        return jsonify({"success": False, "logs": [], "count": 0, "total": 0, "error": str(e)}), 500


@admin_chatlog_bp.route('/<int:log_id>', methods=['DELETE'])
def delete_chat_log(log_id):
    try:
        if not db.connection or not db.connection.is_connected():
            db.connect()
        cursor = db.connection.cursor()
        cursor.execute("SELECT id_log FROM chat_logs WHERE id_log = %s", (log_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"success": False, "error": "Chat log not found"}), 404
        cursor.execute("DELETE FROM chat_logs WHERE id_log = %s", (log_id,))
        db.connection.commit()
        cursor.close()
        return jsonify({"success": True, "deleted": True, "id": log_id})
    except Exception as e:
        print(f"❌ Error deleting chat log {log_id}: {e}")
        if db.connection:
            db.connection.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@admin_chatlog_bp.route('/bulk-delete', methods=['POST'])
def bulk_delete_chat_logs():
    try:
        data = request.get_json() or {}
        ids = data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return jsonify({"success": False, "error": "Invalid or empty 'ids' array"}), 400
        if not db.connection or not db.connection.is_connected():
            db.connect()
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
        return jsonify({"success": True, "deleted_count": deleted_count, "failed": failed})
    except Exception as e:
        print(f"❌ Error in bulk delete: {e}")
        if db.connection:
            db.connection.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@admin_chatlog_bp.route('/stats', methods=['GET'])
def get_chat_stats():
    try:
        if not db.connection or not db.connection.is_connected():
            db.connect()
        cursor = db.connection.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as total FROM chat_logs")
        total_logs = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(DISTINCT id_user) as total FROM chat_logs WHERE id_user IS NOT NULL")
        total_users = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(DISTINCT session_id) as total FROM chat_logs")
        total_sessions = cursor.fetchone()['total']
        cursor.close()
        stats = {"total_logs": total_logs, "total_users": total_users, "total_sessions": total_sessions}
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        print(f"❌ Error getting chat stats: {e}")
        return jsonify({"success": False, "error": str(e)}), 500



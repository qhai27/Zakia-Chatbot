"""
Admin Live Chat Routes - FIXED VERSION
List and respond to escalated live chat requests with proper DB commit.
"""

from flask import Blueprint, request, jsonify
from database import DatabaseManager
import logging
import traceback

admin_livechat_bp = Blueprint('admin_livechat', __name__, url_prefix='/admin/live-chat')

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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


@admin_livechat_bp.route('', methods=['GET'])
def list_live_chat_requests():
    """List live chat requests. Query params: status (open|in_progress|resolved), limit, offset"""
    local_db = DatabaseManager()
    cursor = None
    try:
        status = request.args.get('status', 'open')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))

        if not ensure_connection(local_db):
            return jsonify({"success": False, "requests": [], "count": 0, "total": 0}), 500

        cursor = local_db.connection.cursor(dictionary=True)

        # Count total
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM live_chat_requests
            WHERE status = %s
        """, (status,))
        total = cursor.fetchone()['total']

        # Get requests
        cursor.execute("""
            SELECT
                id,
                session_id,
                user_message,
                bot_response,
                status,
                admin_response,
                admin_name,
                created_at,
                updated_at,
                delivered_at,
                is_delivered
            FROM live_chat_requests
            WHERE status = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (status, limit, offset))

        rows = cursor.fetchall()
        
        # Convert datetime objects to strings for JSON serialization
        for row in rows:
            if row.get('created_at'):
                row['created_at'] = row['created_at'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(row['created_at'], 'strftime') else str(row['created_at'])
            if row.get('updated_at'):
                row['updated_at'] = row['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(row['updated_at'], 'strftime') else str(row['updated_at'])
            if row.get('delivered_at'):
                row['delivered_at'] = row['delivered_at'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(row['delivered_at'], 'strftime') else str(row['delivered_at'])
        
        logger.info(f"📋 Listed {len(rows)} {status} requests")
        
        return jsonify({
            "success": True,
            "requests": rows,
            "count": len(rows),
            "total": total
        })
        
    except Exception as e:
        logger.error(f"❌ Live chat list error: {e}")
        return jsonify({
            "success": False, 
            "requests": [], 
            "count": 0, 
            "total": 0, 
            "error": str(e)
        }), 500
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        try:
            local_db.close()
        except:
            pass


@admin_livechat_bp.route('/history', methods=['GET'])
def history_live_chat_requests():
    """List resolved live chat requests (history). Query params: limit, offset"""
    local_db = DatabaseManager()
    cursor = None
    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))

        if not ensure_connection(local_db):
            return jsonify({"success": False, "requests": [], "count": 0, "total": 0}), 500

        cursor = local_db.connection.cursor(dictionary=True)

        # Count total resolved
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM live_chat_requests
            WHERE status = 'resolved'
        """)
        total = cursor.fetchone()['total']

        # Get resolved requests
        cursor.execute("""
            SELECT
                id,
                session_id,
                user_message,
                bot_response,
                status,
                admin_response,
                admin_name,
                created_at,
                updated_at,
                delivered_at,
                is_delivered
            FROM live_chat_requests
            WHERE status = 'resolved'
            ORDER BY updated_at DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))

        rows = cursor.fetchall()
        
        # Convert datetime objects to strings for JSON serialization
        for row in rows:
            if row.get('created_at'):
                row['created_at'] = row['created_at'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(row['created_at'], 'strftime') else str(row['created_at'])
            if row.get('updated_at'):
                row['updated_at'] = row['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(row['updated_at'], 'strftime') else str(row['updated_at'])
            if row.get('delivered_at'):
                row['delivered_at'] = row['delivered_at'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(row['delivered_at'], 'strftime') else str(row['delivered_at'])
        
        logger.info(f"📋 Listed {len(rows)} resolved requests")
        
        return jsonify({
            "success": True,
            "requests": rows,
            "count": len(rows),
            "total": total
        })
        
    except Exception as e:
        logger.error(f"❌ Live chat history error: {e}")
        return jsonify({
            "success": False, 
            "requests": [], 
            "count": 0, 
            "total": 0, 
            "error": str(e)
        }), 500
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        try:
            local_db.close()
        except:
            pass


@admin_livechat_bp.route('/<int:req_id>/respond', methods=['POST'])
def respond_live_chat_request(req_id):
    """Admin responds to a live chat request - FIXED VERSION"""
    local_db = DatabaseManager()
    cursor = None
    
    try:
        payload = request.get_json(silent=True) or {}
        admin_response = (payload.get('admin_response') or '').strip()
        admin_name = (payload.get('admin_name') or 'Admin').strip()

        if not admin_response:
            return jsonify({
                "success": False, 
                "error": "admin_response is required"
            }), 400

        logger.info(f"\n📤 ADMIN RESPONDING TO REQUEST #{req_id}")
        logger.info(f"   Admin Name: {admin_name}")
        logger.info(f"   Response: {admin_response[:50]}...")

        if not ensure_connection(local_db):
            logger.error("   ❌ DB connection failed")
            return jsonify({
                "success": False, 
                "error": "DB connection failed"
            }), 500

        cursor = local_db.connection.cursor(dictionary=True)
        
        # ===== STEP 1: Verify request exists =====
        logger.info(f"   🔍 Step 1: Checking if request #{req_id} exists...")
        cursor.execute("""
            SELECT id, session_id, status, is_delivered
            FROM live_chat_requests
            WHERE id = %s
        """, (req_id,))
        
        existing = cursor.fetchone()
        
        if not existing:
            cursor.close()
            logger.error(f"   ❌ Request #{req_id} not found in database")
            return jsonify({
                "success": False, 
                "error": f"Request #{req_id} not found"
            }), 404
        
        session_id = existing['session_id']
        logger.info(f"   ✅ Request found!")
        logger.info(f"      Session ID: {session_id[:16] if session_id else 'None'}...")
        logger.info(f"      Current status: {existing['status']}")
        logger.info(f"      Current is_delivered: {existing['is_delivered']}")
        
        # ===== STEP 2: Update with admin response =====
        logger.info(f"   📝 Step 2: Updating request with admin response...")
        
        update_query = """
            UPDATE live_chat_requests
            SET admin_response = %s,
                admin_name = %s,
                status = 'resolved',
                is_delivered = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        cursor.execute(update_query, (admin_response, admin_name, req_id))
        affected_rows = cursor.rowcount
        
        logger.info(f"   📊 Rows affected by UPDATE: {affected_rows}")
        
        if affected_rows == 0:
            logger.warning(f"   ⚠️ Warning: No rows were updated!")
            local_db.connection.rollback()
            cursor.close()
            return jsonify({
                "success": False,
                "error": "Failed to update request - no rows affected"
            }), 500
        
        # ===== STEP 3: COMMIT TO DATABASE =====
        logger.info(f"   💾 Step 3: Committing changes to database...")
        
        # Ensure autocommit mode to make changes immediately visible
        original_autocommit = local_db.connection.autocommit
        local_db.connection.autocommit = False  # Explicit commit mode
        
        local_db.connection.commit()
        logger.info(f"   ✅ COMMIT successful!")
        
        # Restore original autocommit setting
        local_db.connection.autocommit = original_autocommit
        
        # ===== STEP 4: VERIFY the update =====
        logger.info(f"   🔍 Step 4: Verifying the update...")
        cursor.execute("""
            SELECT 
                id, 
                session_id, 
                status, 
                admin_response, 
                admin_name,
                is_delivered,
                updated_at
            FROM live_chat_requests
            WHERE id = %s
        """, (req_id,))
        
        verified = cursor.fetchone()
        
        if verified:
            logger.info(f"   ✅ VERIFICATION SUCCESSFUL!")
            logger.info(f"      Status: {verified['status']}")
            logger.info(f"      Admin Response: {verified['admin_response'][:30] if verified['admin_response'] else 'None'}...")
            logger.info(f"      Admin Name: {verified['admin_name']}")
            logger.info(f"      Is Delivered: {verified['is_delivered']}")
            logger.info(f"      Updated At: {verified['updated_at']}")
            
            # Check if values match what we sent
            if verified['status'] != 'resolved':
                logger.error(f"   ❌ Status not updated! Still: {verified['status']}")
            if verified['admin_response'] != admin_response:
                logger.error(f"   ❌ Admin response not saved correctly!")
            if verified['is_delivered'] != 0:
                logger.error(f"   ❌ is_delivered not set to 0! Value: {verified['is_delivered']}")
                
        else:
            logger.error(f"   ❌ VERIFICATION FAILED - Could not retrieve updated record!")
        
        cursor.close()

        logger.info(f"\n✅ RESPONSE SAVED SUCCESSFULLY!")
        logger.info(f"   User will receive response in next poll (within 5 seconds)")
        logger.info(f"=" * 60)

        return jsonify({
            "success": True,
            "message": "Response saved successfully",
            "id": req_id,
            "session_id": session_id,
            "status": "resolved",
            "admin_name": admin_name,
            "is_delivered": 0,
            "verified": verified is not None
        })
        
    except Exception as e:
        logger.error(f"❌ Live chat respond error: {e}")
        logger.error(traceback.format_exc())
        
        if local_db.connection:
            try:
                local_db.connection.rollback()
                logger.info("   🔄 Transaction rolled back")
            except Exception as rb_error:
                logger.error(f"   ❌ Rollback error: {rb_error}")
        
        return jsonify({
            "success": False, 
            "error": str(e)
        }), 500
        
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        try:
            local_db.close()
        except:
            pass


@admin_livechat_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get live chat statistics"""
    local_db = DatabaseManager()
    cursor = None
    try:
        if not ensure_connection(local_db):
            return jsonify({"success": False}), 500

        cursor = local_db.connection.cursor(dictionary=True)
        
        # Count by status
        cursor.execute("""
            SELECT 
                status,
                COUNT(*) as count
            FROM live_chat_requests
            GROUP BY status
        """)
        
        stats = {}
        for row in cursor.fetchall():
            stats[row['status']] = row['count']
        
        cursor.close()
        
        return jsonify({
            "success": True,
            "stats": {
                "open": stats.get('open', 0),
                "in_progress": stats.get('in_progress', 0),
                "resolved": stats.get('resolved', 0),
                "total": sum(stats.values())
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Stats error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        try:
            local_db.close()
        except:
            pass


@admin_livechat_bp.route('/debug/<int:req_id>', methods=['GET'])
def debug_request(req_id):
    """Debug endpoint to check request status"""
    local_db = DatabaseManager()
    cursor = None
    try:
        if not ensure_connection(local_db):
            return jsonify({"success": False, "error": "DB connection failed"}), 500

        cursor = local_db.connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT *
            FROM live_chat_requests
            WHERE id = %s
        """, (req_id,))
        
        row = cursor.fetchone()
        cursor.close()
        
        if not row:
            return jsonify({
                "success": False,
                "error": f"Request #{req_id} not found"
            }), 404
        
        return jsonify({
            "success": True,
            "request": row
        })
        
    except Exception as e:
        logger.error(f"❌ Debug error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        try:
            local_db.close()
        except:
            pass


@admin_livechat_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        db_connected = ensure_connection(db)
        return jsonify({
            "success": True,
            "service": "admin_livechat",
            "status": "operational",
            "database": "connected" if db_connected else "disconnected"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
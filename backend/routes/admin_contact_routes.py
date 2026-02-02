"""
Admin Contact Request Routes
Manage and respond to user contact requests
"""

from flask import Blueprint, request, jsonify
from database import DatabaseManager
import logging
import traceback
import json

admin_contact_bp = Blueprint('admin_contact', __name__, url_prefix='/admin/contact-requests')

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


@admin_contact_bp.route('', methods=['GET'])
def list_contact_requests():
    """
    List contact requests
    
    Query params:
    - status: pending|contacted|resolved (default: pending)
    - limit: int (default: 100)
    - offset: int (default: 0)
    
    Returns:
        JSON with list of contact requests
    """
    local_db = DatabaseManager()
    cursor = None
    
    try:
        status = request.args.get('status', 'pending')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        logger.info(f"📋 Listing contact requests: status={status}, limit={limit}, offset={offset}")
        
        if not ensure_connection(local_db):
            return jsonify({
                "success": False,
                "requests": [],
                "count": 0,
                "total": 0
            }), 500
        
        cursor = local_db.connection.cursor(dictionary=True)
        
        # Count total
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM contact_requests
            WHERE status = %s
        """, (status,))
        total = cursor.fetchone()['total']
        
        # Get requests
        cursor.execute("""
            SELECT
                id, session_id, name, phone, email, question,
                preferred_contact_method, trigger_type, status,
                admin_notes, contacted_by, created_at, contacted_at, updated_at
            FROM contact_requests
            WHERE status = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (status, limit, offset))
        
        rows = cursor.fetchall()
        
        # Convert datetime objects to strings
        for row in rows:
            if row.get('created_at'):
                row['created_at'] = row['created_at'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(row['created_at'], 'strftime') else str(row['created_at'])
            if row.get('contacted_at'):
                row['contacted_at'] = row['contacted_at'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(row['contacted_at'], 'strftime') else str(row['contacted_at'])
            if row.get('updated_at'):
                row['updated_at'] = row['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(row['updated_at'], 'strftime') else str(row['updated_at'])
        
        logger.info(f"✅ Listed {len(rows)} {status} requests (total: {total})")
        
        return jsonify({
            "success": True,
            "requests": rows,
            "count": len(rows),
            "total": total
        })
        
    except Exception as e:
        logger.error(f"❌ List contact requests error: {e}")
        traceback.print_exc()
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


@admin_contact_bp.route('/history', methods=['GET'])
def history_contact_requests():
    """
    List contacted/resolved contact requests (history)
    
    Query params:
    - limit: int (default: 100)
    - offset: int (default: 0)
    
    Returns:
        JSON with list of contacted/resolved requests
    """
    local_db = DatabaseManager()
    cursor = None
    
    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        if not ensure_connection(local_db):
            return jsonify({
                "success": False,
                "requests": [],
                "count": 0,
                "total": 0
            }), 500
        
        cursor = local_db.connection.cursor(dictionary=True)
        
        # Count total resolved/contacted
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM contact_requests
            WHERE status IN ('contacted', 'resolved')
        """)
        total = cursor.fetchone()['total']
        
        # Get requests
        cursor.execute("""
            SELECT
                id, session_id, name, phone, email, question,
                preferred_contact_method, trigger_type, status,
                admin_notes, contacted_by, contact_method_used,
                created_at, contacted_at, updated_at
            FROM contact_requests
            WHERE status IN ('contacted', 'resolved')
            ORDER BY contacted_at DESC, updated_at DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))
        
        rows = cursor.fetchall()
        
        # Convert datetime objects
        for row in rows:
            if row.get('created_at'):
                row['created_at'] = row['created_at'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(row['created_at'], 'strftime') else str(row['created_at'])
            if row.get('contacted_at'):
                row['contacted_at'] = row['contacted_at'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(row['contacted_at'], 'strftime') else str(row['contacted_at'])
            if row.get('updated_at'):
                row['updated_at'] = row['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(row['updated_at'], 'strftime') else str(row['updated_at'])
        
        logger.info(f"✅ Listed {len(rows)} history requests")
        
        return jsonify({
            "success": True,
            "requests": rows,
            "count": len(rows),
            "total": total
        })
        
    except Exception as e:
        logger.error(f"❌ History error: {e}")
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


@admin_contact_bp.route('/<int:req_id>/mark-contacted', methods=['POST'])
def mark_contacted(req_id):
    """
    Mark a contact request as contacted
    
    Expected JSON payload:
    {
        "admin_notes": "Called customer, issue resolved",
        "contact_method_used": "whatsapp",
        "contacted_by": "Admin Name"
    }
    
    Returns:
        JSON with success status
    """
    local_db = DatabaseManager()
    cursor = None
    
    try:
        payload = request.get_json(silent=True) or {}
        admin_notes = (payload.get('admin_notes') or '').strip()
        contact_method = (payload.get('contact_method_used') or 'whatsapp').strip()
        contacted_by = (payload.get('contacted_by') or 'Admin').strip()
        
        logger.info(f"\n✅ MARKING REQUEST #{req_id} AS CONTACTED")
        logger.info(f"   Contacted by: {contacted_by}")
        logger.info(f"   Method: {contact_method}")
        logger.info(f"   Notes: {admin_notes[:50]}...")
        
        if not ensure_connection(local_db):
            return jsonify({
                "success": False,
                "error": "Database connection failed"
            }), 500
        
        cursor = local_db.connection.cursor(dictionary=True)
        
        # Check if request exists
        cursor.execute("""
            SELECT id, name, phone FROM contact_requests WHERE id = %s
        """, (req_id,))
        
        existing = cursor.fetchone()
        
        if not existing:
            logger.error(f"❌ Request #{req_id} not found")
            cursor.close()
            return jsonify({
                "success": False,
                "error": f"Request #{req_id} not found"
            }), 404
        
        logger.info(f"   Found request for: {existing['name']} ({existing['phone']})")
        
        # Update request
        cursor.execute("""
            UPDATE contact_requests
            SET status = 'contacted',
                contacted_at = CURRENT_TIMESTAMP,
                admin_notes = %s,
                contact_method_used = %s,
                contacted_by = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (admin_notes, contact_method, contacted_by, req_id))
        
        affected = cursor.rowcount
        local_db.connection.commit()
        
        logger.info(f"   ✅ Updated {affected} rows")
        
        cursor.close()
        
        return jsonify({
            "success": True,
            "id": req_id,
            "status": "contacted"
        })
        
    except Exception as e:
        logger.error(f"❌ Mark contacted error: {e}")
        traceback.print_exc()
        
        if local_db.connection:
            try:
                local_db.connection.rollback()
            except:
                pass
        
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


@admin_contact_bp.route('/<int:req_id>', methods=['DELETE'])
def delete_contact_request(req_id):
    """
    Delete a contact request
    
    Returns:
        JSON with success status
    """
    local_db = DatabaseManager()
    cursor = None
    
    try:
        if not ensure_connection(local_db):
            return jsonify({
                "success": False,
                "error": "Database connection failed"
            }), 500
        
        cursor = local_db.connection.cursor(dictionary=True)
        
        # Check if exists
        cursor.execute("""
            SELECT id FROM contact_requests WHERE id = %s
        """, (req_id,))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({
                "success": False,
                "error": "Not found"
            }), 404
        
        # Delete
        cursor.execute("""
            DELETE FROM contact_requests WHERE id = %s
        """, (req_id,))
        
        deleted = cursor.rowcount > 0
        
        if deleted:
            local_db.connection.commit()
            logger.info(f"✅ Deleted contact request #{req_id}")
        else:
            local_db.connection.rollback()
            cursor.close()
            return jsonify({
                "success": False,
                "error": "Not found"
            }), 404
        
        cursor.close()
        
        return jsonify({
            "success": True,
            "id": req_id,
            "deleted": True
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Delete error: {e}")
        traceback.print_exc()
        
        if local_db.connection:
            try:
                local_db.connection.rollback()
            except:
                pass
        
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


@admin_contact_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get contact request statistics"""
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
            FROM contact_requests
            GROUP BY status
        """)
        
        stats = {}
        for row in cursor.fetchall():
            stats[row['status']] = row['count']
        
        cursor.close()
        
        return jsonify({
            "success": True,
            "stats": {
                "pending": stats.get('pending', 0),
                "contacted": stats.get('contacted', 0),
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


@admin_contact_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        db_connected = ensure_connection(db)
        return jsonify({
            "success": True,
            "service": "admin_contact",
            "status": "operational",
            "database": "connected" if db_connected else "disconnected"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
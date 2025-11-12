"""
Admin Reminder Routes for ZAKIA Chatbot
Handles reminder management endpoints for admin panel
"""

from flask import Blueprint, request, jsonify
from database import DatabaseManager
from reminder_model import ReminderManager

# Create blueprint
admin_reminder_bp = Blueprint('admin_reminder', __name__, url_prefix='/admin/reminders')

# Initialize database and reminder manager
db = DatabaseManager()
rm = None  # Will be initialized on first request

def get_reminder_manager():
    """Get or create reminder manager instance"""
    global rm
    if rm is None:
        try:
            # Ensure database connection
            if not db.connection or not db.connection.is_connected():
                if not db.connect():
                    print("❌ Failed to connect to database in get_reminder_manager")
                    raise Exception("Database connection failed")
            
            rm = ReminderManager(db, auto_create=True)
            # Ensure table exists (this is safe to call multiple times)
            if not rm.create_reminder_table():
                print("⚠️ Warning: Could not create reminders table, but continuing anyway")
        except Exception as e:
            print(f"❌ Error initializing reminder manager: {e}")
            import traceback
            traceback.print_exc()
            # Re-raise to let the route handler catch it
            raise
    return rm

@admin_reminder_bp.route('', methods=['GET'])
def list_reminders():
    """
    List all reminders with optional filtering
    Query params: 
    - limit: number of records (default: 100)
    - offset: starting position (default: 0)
    - search: search term for name, IC, or phone
    - zakat_type: filter by zakat type (pendapatan/simpanan)
    
    Returns:
    {
        "success": true,
        "reminders": [...],
        "count": 10
    }
    """
    try:
        # Parse query parameters
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        search = request.args.get('search', '').strip()
        zakat_type = request.args.get('zakat_type', '').strip()
        
        # Ensure database connection
        if not db.connection or not db.connection.is_connected():
            print("⚠️ Database not connected, attempting to connect...")
            if not db.connect():
                print("❌ Database connection failed")
                return jsonify({
                    "success": False,
                    "reminders": [],
                    "count": 0,
                    "error": "Database connection failed"
                }), 500
            print("✅ Database connected successfully")
        
        # Get reminder manager and fetch reminders
        try:
            manager = get_reminder_manager()
        except Exception as mgr_error:
            print(f"❌ Failed to get reminder manager: {mgr_error}")
            return jsonify({
                "success": False,
                "reminders": [],
                "error": "Failed to initialize reminder manager"
            }), 500
        
        # Fetch reminders with error handling
        try:
            reminders = manager.list(
                limit=limit,
                offset=offset,
                search=search,
                zakat_type=zakat_type
            )
            
            # Ensure reminders is a list
            if not isinstance(reminders, list):
                print("⚠️ manager.list() did not return a list, converting...")
                reminders = []
            
            # Log success for debugging
            print(f"✅ Successfully fetched {len(reminders)} reminders")
            
            return jsonify({
                "success": True,
                "reminders": reminders,
                "count": len(reminders)
            })
        except Exception as list_error:
            print(f"❌ Error in manager.list(): {list_error}")
            import traceback
            traceback.print_exc()
            # Return error response instead of empty success
            return jsonify({
                "success": False,
                "reminders": [],
                "count": 0,
                "error": f"Failed to fetch reminders: {str(list_error)}"
            }), 500
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "reminders": [],
            "error": f"Invalid parameter: {str(e)}"
        }), 400
        
    except Exception as e:
        print(f"Error listing reminders: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "reminders": [],
            "error": str(e)
        }), 500

@admin_reminder_bp.route('/stats', methods=['GET'])
def get_stats():
    """
    Get reminder statistics
    
    Returns:
    {
        "success": true,
        "stats": {
            "total": 25,
            "total_amount": 15000.00,
            "by_type": [
                {"zakat_type": "pendapatan", "count": 15, "amount": 10000.00},
                {"zakat_type": "simpanan", "count": 10, "amount": 5000.00}
            ]
        }
    }
    """
    try:
        # Ensure database connection
        if not db.connection or not db.connection.is_connected():
            print("⚠️ Database not connected for stats, attempting to connect...")
            if not db.connect():
                print("❌ Database connection failed for stats")
                return jsonify({
                    "success": False,
                    "error": "Database connection failed"
                }), 500
            print("✅ Database connected successfully for stats")
        
        # Get reminder manager (this will ensure table exists)
        try:
            manager = get_reminder_manager()
        except Exception as mgr_error:
            print(f"❌ Failed to get reminder manager for stats: {mgr_error}")
            return jsonify({
                "success": False,
                "error": "Failed to initialize reminder manager"
            }), 500
        
        # Get stats with error handling
        try:
            stats = manager.get_stats()
            
            # Validate stats structure
            if not isinstance(stats, dict):
                print("⚠️ manager.get_stats() did not return a dict, using defaults")
                stats = {'total': 0, 'total_amount': 0, 'by_type': []}
            
            # Ensure all required fields exist
            if 'total' not in stats:
                stats['total'] = 0
            if 'total_amount' not in stats:
                stats['total_amount'] = 0
            if 'by_type' not in stats:
                stats['by_type'] = []
            
            print(f"✅ Successfully fetched stats: {stats.get('total', 0)} reminders")
            
            return jsonify({
                "success": True,
                "stats": stats
            })
        except Exception as stats_error:
            print(f"❌ Error in manager.get_stats(): {stats_error}")
            import traceback
            traceback.print_exc()
            # Return empty stats instead of failing
            return jsonify({
                "success": True,
                "stats": {'total': 0, 'total_amount': 0, 'by_type': []}
            })
        
    except Exception as e:
        print(f"Error getting stats: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@admin_reminder_bp.route('/<int:reminder_id>', methods=['GET'])
def get_reminder(reminder_id):
    """
    Get single reminder by ID
    
    Args:
        reminder_id: The ID of the reminder
    
    Returns:
    {
        "success": true,
        "reminder": {...}
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
        
        # Get reminder
        manager = get_reminder_manager()
        reminder = manager.get_by_id(reminder_id)
        
        if not reminder:
            return jsonify({
                "success": False,
                "error": "Reminder not found"
            }), 404
        
        return jsonify({
            "success": True,
            "reminder": reminder
        })
        
    except Exception as e:
        print(f"Error getting reminder {reminder_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@admin_reminder_bp.route('/<int:reminder_id>', methods=['DELETE'])
def delete_reminder(reminder_id):
    """
    Delete a reminder by ID
    
    Args:
        reminder_id: The ID of the reminder to delete
    
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
        
        # Delete reminder
        manager = get_reminder_manager()
        success = manager.delete(reminder_id)
        
        if success:
            return jsonify({
                "success": True,
                "deleted": True,
                "id": reminder_id
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to delete reminder or reminder not found"
            }), 404
            
    except Exception as e:
        print(f"Error deleting reminder {reminder_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Health check endpoint for this blueprint
@admin_reminder_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for admin reminder routes"""
    try:
        # Test database connection
        if not db.connection or not db.connection.is_connected():
            db.connect()
        
        # Test reminder manager
        manager = get_reminder_manager()
        
        return jsonify({
            "status": "healthy",
            "message": "Admin reminder routes operational",
            "database_connected": db.connection.is_connected() if db.connection else False
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500
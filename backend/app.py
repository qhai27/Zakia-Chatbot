"""
ZAKIA Chatbot - Main Application
Bulletproof version with comprehensive error handling
"""

from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
# Configure CORS to allow preflight requests from all origins
CORS(app, 
     origins="*",
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=False)

print("🚀 Starting ZAKIA Chatbot...")
print("=" * 60)

# Track which blueprints were successfully loaded
loaded_blueprints = []
failed_blueprints = []

# Import and register chat routes
try:
    from routes.chat_routes import chat_bp
    app.register_blueprint(chat_bp)
    loaded_blueprints.append("✅ Chat routes")
    print("✅ Chat routes loaded successfully")
except ImportError as e:
    failed_blueprints.append(f"❌ Chat routes: {e}")
    print(f"❌ Failed to load chat routes: {e}")

# Import and register admin routes
try:
    from routes.admin_routes import admin_bp
    app.register_blueprint(admin_bp)
    loaded_blueprints.append("✅ Admin routes")
    print("✅ Admin routes loaded successfully")
except ImportError as e:
    failed_blueprints.append(f"❌ Admin routes: {e}")
    print(f"❌ Failed to load admin routes: {e}")

# Import and register zakat routes
try:
    from routes.zakat_routes import zakat_bp
    app.register_blueprint(zakat_bp)
    loaded_blueprints.append("✅ Zakat routes")
    print("✅ Zakat routes loaded successfully")
except ImportError as e:
    failed_blueprints.append(f"❌ Zakat routes: {e}")
    print(f"❌ Failed to load zakat routes: {e}")

# Import and register reminder routes
try:
    from routes.reminder_routes import reminder_bp
    app.register_blueprint(reminder_bp)
    loaded_blueprints.append("✅ Reminder routes")
    print("✅ Reminder routes loaded successfully")
except ImportError as e:
    failed_blueprints.append(f"❌ Reminder routes: {e}")
    print(f"⚠️ Failed to load reminder routes from file: {e}")
    print("⚠️ Creating inline reminder routes as fallback...")
    
    # Create inline reminder routes
    try:
        from flask import Blueprint, request, jsonify
        from database import DatabaseManager
        from reminder_model import ReminderManager
        import datetime
        
        reminder_bp = Blueprint('reminder', __name__)
        db = DatabaseManager()
        
        @reminder_bp.route('/api/save-reminder', methods=['POST'])
        def save_reminder():
            payload = request.get_json(silent=True) or {}
            name = (payload.get('name') or '').strip()
            ic_number = (payload.get('ic_number') or '').strip()
            phone = (payload.get('phone') or '').strip()
            zakat_type = (payload.get('zakat_type') or 'umum').strip()
            year = (payload.get('year') or '').strip()
            
            try:
                zakat_amount = float(payload.get('zakat_amount')) if payload.get('zakat_amount') not in (None, '') else None
            except:
                zakat_amount = None
            
            if not name or not ic_number or not phone:
                return jsonify({'success': False, 'error': 'Sila lengkapkan maklumat.'}), 400
            
            try:
                if not db.connection or not db.connection.is_connected():
                    db.connect()
                
                rm = ReminderManager(db)
                result = rm.save({
                    'name': name,
                    'ic_number': ic_number.replace('-', '').replace(' ', ''),
                    'phone': phone,
                    'zakat_type': zakat_type,
                    'zakat_amount': zakat_amount,
                    'year': year
                })
                
                if result.get('success'):
                    first_name = name.split(' ')[0]
                    return jsonify({
                        'success': True,
                        'reply': f"✅ Terima kasih {first_name}. Maklumat peringatan telah disimpan.",
                        'id': result.get('id')
                    })
                else:
                    return jsonify({'success': False, 'error': result.get('error', 'Gagal menyimpan.')}), 500
            except Exception as e:
                print(f"Save reminder error: {e}")
                return jsonify({'success': False, 'error': 'Ralat sistem.'}), 500
        
        app.register_blueprint(reminder_bp)
        loaded_blueprints.append("✅ Reminder routes (inline)")
        print("✅ Inline reminder routes created successfully")
    except Exception as e:
        failed_blueprints.append(f"❌ Inline reminder routes: {e}")
        print(f"❌ Failed to create inline reminder routes: {e}")

# Import and register admin reminder routes
try:
    from routes.admin_reminder_routes import admin_reminder_bp
    app.register_blueprint(admin_reminder_bp)
    loaded_blueprints.append("✅ Admin reminder routes")
    print("✅ Admin reminder routes loaded successfully")
except ImportError as e:
    print(f"⚠️ Failed to load admin reminder routes from file: {e}")
    print("⚠️ Creating inline admin reminder routes as fallback...")
    
    # Create inline admin reminder routes
    try:
        from flask import Blueprint, request, jsonify
        from database import DatabaseManager
        from reminder_model import ReminderManager
        
        admin_reminder_bp = Blueprint('admin_reminder', __name__, url_prefix='/admin/reminders')
        db_mgr = DatabaseManager()
        
        @admin_reminder_bp.route('', methods=['GET'])
        def list_reminders():
            try:
                limit = int(request.args.get('limit', 100))
                offset = int(request.args.get('offset', 0))
                search = request.args.get('search', '').strip()
                zakat_type = request.args.get('zakat_type', '').strip()
                
                if not db_mgr.connection or not db_mgr.connection.is_connected():
                    db_mgr.connect()
                
                rm = ReminderManager(db_mgr)
                reminders = rm.list(limit=limit, offset=offset, search=search, zakat_type=zakat_type)
                
                return jsonify({"success": True, "reminders": reminders, "count": len(reminders)})
            except Exception as e:
                print(f"List reminders error: {e}")
                return jsonify({"success": False, "reminders": [], "error": str(e)}), 500
        
        @admin_reminder_bp.route('/stats', methods=['GET'])
        def get_stats():
            try:
                if not db_mgr.connection or not db_mgr.connection.is_connected():
                    db_mgr.connect()
                
                rm = ReminderManager(db_mgr)
                stats = rm.get_stats()
                
                return jsonify({"success": True, "stats": stats})
            except Exception as e:
                print(f"Get stats error: {e}")
                return jsonify({"success": False, "error": str(e)}), 500
        
        @admin_reminder_bp.route('/<int:reminder_id>', methods=['GET'])
        def get_reminder(reminder_id):
            try:
                if not db_mgr.connection or not db_mgr.connection.is_connected():
                    db_mgr.connect()
                
                rm = ReminderManager(db_mgr)
                reminder = rm.get_by_id(reminder_id)
                
                if not reminder:
                    return jsonify({"success": False, "error": "Not found"}), 404
                
                return jsonify({"success": True, "reminder": reminder})
            except Exception as e:
                print(f"Get reminder error: {e}")
                return jsonify({"success": False, "error": str(e)}), 500
        
        @admin_reminder_bp.route('/<int:reminder_id>', methods=['DELETE'])
        def delete_reminder(reminder_id):
            try:
                if not db_mgr.connection or not db_mgr.connection.is_connected():
                    db_mgr.connect()
                
                rm = ReminderManager(db_mgr)
                success = rm.delete(reminder_id)
                
                if success:
                    return jsonify({"success": True, "deleted": True, "id": reminder_id})
                else:
                    return jsonify({"success": False, "error": "Failed to delete"}), 404
            except Exception as e:
                print(f"Delete reminder error: {e}")
                return jsonify({"success": False, "error": str(e)}), 500
        
        app.register_blueprint(admin_reminder_bp)
        loaded_blueprints.append("✅ Admin reminder routes (inline)")
        print("✅ Inline admin reminder routes created successfully")
    except Exception as e:
        failed_blueprints.append(f"❌ Inline admin reminder routes: {e}")
        print(f"❌ Failed to create inline admin reminder routes: {e}")

print("=" * 60)

# Summary
print("\n📊 Blueprint Loading Summary:")
for bp in loaded_blueprints:
    print(f"  {bp}")

if failed_blueprints:
    print("\n⚠️ Failed Blueprints:")
    for bp in failed_blueprints:
        print(f"  {bp}")

print("\n" + "=" * 60)

if __name__ == "__main__":
    # Initialize database
    try:
        from services.database_service import DatabaseService
        
        db_service = DatabaseService()
        if db_service.initialize_database():
            print("✅ Database initialized successfully")
            
            # Initialize reminder table
            try:
                from reminder_model import ReminderManager
                db_manager = db_service.get_database_manager()
                reminder_mgr = ReminderManager(db_manager)
                
                if reminder_mgr.create_reminder_table():
                    print("✅ Reminder table initialized successfully")
                else:
                    print("⚠️ Warning: Failed to initialize reminder table")
            except Exception as e:
                print(f"⚠️ Warning: Reminder table initialization error: {e}")
            
            # Initialize NLP model
            try:
                from services.nlp_service import NLPService
                nlp_service = NLPService()
                nlp_service.initialize_nlp()
                print("✅ NLP model initialized successfully")
            except Exception as e:
                print(f"⚠️ Warning: NLP initialization error: {e}")
            
            print("=" * 60)
            print("🌐 Flask server starting on http://localhost:5000")
            print("\n📋 Available endpoints:")
            print("   💬 Chat: POST /chat")
            print("   💰 Zakat Calculator: POST /api/calculate-zakat")
            print("   📅 Zakat Years: GET /api/zakat/years")
            print("   📊 Zakat Nisab Info: GET /api/zakat/nisab-info")
            print("   🔔 Save Reminder: POST /api/save-reminder")
            print("   📋 List Reminders: GET /api/reminders")
            print("   👨‍💼 Admin FAQs: GET /admin/faqs")
            print("   👨‍💼 Admin Reminders: GET /admin/reminders")
            print("   📊 Reminder Stats: GET /admin/reminders/stats")
            print("   ❤️ Health Check: GET /health")
            print("=" * 60 + "\n")
            
            app.run(host="0.0.0.0", port=5000, debug=True)
        else:
            print("❌ Failed to initialize database")
            print("\n🔧 Troubleshooting steps:")
            print("  1. Check if MySQL is running")
            print("  2. Verify credentials in backend/database.py")
            print("  3. Ensure database 'lznk_chatbot' exists")
            print("  4. Check MySQL connection settings")
    except Exception as e:
        print(f"❌ Startup error: {e}")
        import traceback
        traceback.print_exc()
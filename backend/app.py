from flask import Flask
from flask_cors import CORS
from routes.chat_routes import chat_bp
from routes.admin_routes import admin_bp
from routes.zakat_routes import zakat_bp
from routes.reminder_routes import reminder_bp  # Add reminder routes
from services.database_service import DatabaseService
from services.nlp_service import NLPService
from reminder_model import ReminderManager  # Import reminder manager

app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(chat_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(zakat_bp)
app.register_blueprint(reminder_bp)  # Register reminder routes

if __name__ == "__main__":
    print("🚀 Starting ZAKIA Chatbot...")
    
    # Initialize database
    db_service = DatabaseService()
    if db_service.initialize_database():
        print("✅ Database initialized successfully")
        
        # Initialize reminder table
        db_manager = db_service.get_database_manager()
        reminder_mgr = ReminderManager(db_manager)
        if reminder_mgr.create_reminder_table():
            print("✅ Reminder system initialized successfully")
        else:
            print("⚠️ Warning: Failed to initialize reminder table")
        
        # Initialize and train NLP model
        nlp_service = NLPService()
        nlp_service.initialize_nlp()
        print("✅ NLP model initialized successfully")
        
        print("🌐 Starting Flask server on http://localhost:5000")
        print("💰 Zakat calculator available at /calculate-zakat")
        print("🔔 Reminder system available at /save-reminder")
        app.run(host="0.0.0.0", port=5000, debug=True)
    else:
        print("❌ Failed to initialize database")
        print("Please check your MySQL connection and try again.")
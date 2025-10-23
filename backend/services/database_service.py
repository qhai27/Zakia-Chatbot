"""
Database Service for ZAKIA Chatbot
Handles database initialization and connection
"""

from database import DatabaseManager

class DatabaseService:
    def __init__(self):
        self.db = DatabaseManager()
    
    def initialize_database(self):
        """Initialize database and tables"""
        print("🗄️ Initializing database...")
        
        # Create database
        if not self.db.create_database():
            print("❌ Failed to create database")
            return False
        
        # Connect to database
        if not self.db.connect():
            print("❌ Failed to connect to database")
            return False
        
        # Create tables
        if not self.db.create_tables():
            print("❌ Failed to create tables")
            return False
        
        # Insert FAQ data
        if not self.db.insert_faqs():
            print("❌ Failed to insert FAQ data")
            return False
        
        print("✅ Database initialized successfully")
        return True
    
    def get_database_manager(self):
        """Get the database manager instance"""
        return self.db

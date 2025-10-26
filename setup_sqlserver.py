#!/usr/bin/env python3
"""
SQL Server Setup Script for ZAKIA Chatbot
This script will initialize the SQL Server database and insert FAQ data
"""

import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def main():
    print("🗄️ ZAKIA Chatbot SQL Server Setup")
    print("=" * 50)
    
    try:
        from sqlserver_database import SQLServerDatabaseManager
        
        # Create database manager
        db = SQLServerDatabaseManager()
        
        print("1. Creating database...")
        if not db.create_database():
            print("❌ Failed to create database")
            print("Please check your SQL Server connection and credentials.")
            return False
        
        print("✅ Database created successfully")
        
        print("2. Connecting to database...")
        if not db.connect():
            print("❌ Failed to connect to database")
            print("Please check your SQL Server connection and credentials.")
            return False
        
        print("✅ Connected to database")
        
        print("3. Creating tables...")
        if not db.create_tables():
            print("❌ Failed to create tables")
            return False
        
        print("✅ Tables created successfully")
        
        print("4. Inserting FAQ data...")
        if not db.insert_faqs():
            print("❌ Failed to insert FAQ data")
            return False
        
        print("✅ FAQ data inserted successfully")
        
        print("5. Testing FAQ retrieval...")
        faqs = db.get_faqs()
        if faqs:
            print(f"✅ Retrieved {len(faqs)} FAQs from database")
        else:
            print("❌ No FAQs found in database")
            return False
        
        # Close connection
        db.close()
        
        print("\n🎉 SQL Server setup completed successfully!")
        print("You can now start the chatbot with: python start_chatbot.py")
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Please install SQL Server dependencies:")
        print("pip install pyodbc sqlalchemy pandas")
        return False
        
    except Exception as e:
        print(f"❌ Error setting up SQL Server: {e}")
        print("Please check your SQL Server connection and try again.")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n💡 Troubleshooting Tips:")
        print("1. Make sure SQL Server is running")
        print("2. Check your SQL Server credentials in backend/sqlserver_database.py")
        print("3. Verify the database 'lznk_chatbot' exists")
        print("4. Check your SQL Server user permissions")
        print("5. Install Microsoft ODBC Driver 17 for SQL Server")
        sys.exit(1)


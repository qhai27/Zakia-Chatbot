#!/usr/bin/env python3
"""
SQL Server Connection Test for ZAKIA Chatbot
This script tests your SQL Server connection and helps you configure it
"""

import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_sqlserver_connection():
    """Test SQL Server connection with current settings"""
    try:
        from sqlserver_database import SQLServerDatabaseManager
        
        print("🔍 Testing SQL Server Connection...")
        print("=" * 50)
        
        # Create database manager
        db = SQLServerDatabaseManager()
        
        print(f"Server: {db.server}")
        print(f"Database: {db.database}")
        print(f"Username: {db.username}")
        print(f"Password: {'*' * len(db.password) if db.password else 'Empty'}")
        print()
        
        # Test connection
        if db.connect():
            print("✅ SQL Server connection successful!")
            
            # Test database creation
            if db.create_database():
                print("✅ Database creation successful!")
            else:
                print("❌ Database creation failed!")
                return False
            
            # Test table creation
            if db.create_tables():
                print("✅ Table creation successful!")
            else:
                print("❌ Table creation failed!")
                return False
            
            # Test FAQ insertion
            if db.insert_faqs():
                print("✅ FAQ data insertion successful!")
            else:
                print("❌ FAQ data insertion failed!")
                return False
            
            # Test FAQ retrieval
            faqs = db.get_faqs()
            if faqs:
                print(f"✅ FAQ retrieval successful! Found {len(faqs)} FAQs")
            else:
                print("❌ FAQ retrieval failed!")
                return False
            
            db.close()
            print("\n🎉 All SQL Server operations successful!")
            return True
            
        else:
            print("❌ SQL Server connection failed!")
            print("\n💡 Common solutions:")
            print("1. Check if SQL Server is running")
            print("2. Verify your username and password")
            print("3. Make sure the database 'lznk_chatbot' exists")
            print("4. Check your SQL Server user privileges")
            print("5. Install Microsoft ODBC Driver 17 for SQL Server")
            return False
            
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Please install SQL Server dependencies:")
        print("pip install pyodbc sqlalchemy pandas")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Check your SQL Server configuration in backend/sqlserver_database.py")
        return False

def show_config_help():
    """Show configuration help"""
    print("\n🔧 SQL Server Configuration Help:")
    print("=" * 50)
    print("To fix connection issues, edit backend/sqlserver_database.py:")
    print()
    print("def __init__(self, server=None, database=None, username=None, password=None):")
    print("    self.server = server or 'localhost'  # or 'localhost\\SQLEXPRESS' for Express")
    print("    self.database = database or 'lznk_chatbot'")
    print("    self.username = username or 'sa'  # Your SQL Server username")
    print("    self.password = password or 'your_password'  # Your SQL Server password")
    print()
    print("Common SQL Server configurations:")
    print("- SQL Server Express: server = 'localhost\\SQLEXPRESS'")
    print("- SQL Server Developer: server = 'localhost'")
    print("- Named Instance: server = 'localhost\\INSTANCENAME'")
    print("- Remote Server: server = '192.168.1.100'")
    print()
    print("Common usernames:")
    print("- 'sa' (system administrator)")
    print("- 'lznk_user' (if you created a custom user)")
    print()
    print("If you don't have a password, use: ''")
    print("If you have a password, use: 'your_actual_password'")

def main():
    print("🗄️ ZAKIA Chatbot SQL Server Connection Test")
    print("=" * 50)
    
    success = test_sqlserver_connection()
    
    if not success:
        show_config_help()
        print("\n🚀 After fixing the configuration, run:")
        print("   python test_sqlserver_connection.py")
        return False
    
    print("\n✅ SQL Server connection is working perfectly!")
    print("🚀 You can now start the chatbot with:")
    print("   python start_chatbot.py")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)


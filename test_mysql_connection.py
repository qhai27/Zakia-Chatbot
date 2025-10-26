#!/usr/bin/env python3
"""
MySQL Connection Test for ZAKIA Chatbot
This script tests your MySQL connection and helps you configure it
"""

import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_mysql_connection():
    """Test MySQL connection with current settings"""
    try:
        from database import DatabaseManager
        
        print("🔍 Testing MySQL Connection...")
        print("=" * 50)
        
        # Create database manager
        db = DatabaseManager()
        
        print(f"Host: {db.host}")
        print(f"User: {db.user}")
        print(f"Database: {db.database}")
        print(f"Password: {'*' * len(db.password) if db.password else 'Empty'}")
        print()
        
        # Test connection
        if db.connect():
            print("✅ MySQL connection successful!")
            
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
            print("\n🎉 All MySQL operations successful!")
            return True
            
        else:
            print("❌ MySQL connection failed!")
            print("\n💡 Common solutions:")
            print("1. Check if MySQL is running")
            print("2. Verify your username and password")
            print("3. Make sure the database 'lznk_chatbot' exists")
            print("4. Check your MySQL user privileges")
            return False
            
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Please install dependencies: pip install -r backend/requirement.txt")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Check your MySQL configuration in backend/database.py")
        return False

def show_config_help():
    """Show configuration help"""
    print("\n🔧 Configuration Help:")
    print("=" * 50)
    print("To fix connection issues, edit backend/database.py:")
    print()
    print("def __init__(self, host=None, user=None, password=None, database=None):")
    print("    self.host = host or 'localhost'")
    print("    self.user = user or 'root'  # Your MySQL username")
    print("    self.password = password or 'your_password'  # Your MySQL password")
    print("    self.database = database or 'lznk_chatbot'")
    print()
    print("Common MySQL usernames:")
    print("- 'root' (default)")
    print("- 'lznk_user' (if you created a custom user)")
    print()
    print("If you don't have a password, use: ''")
    print("If you have a password, use: 'your_actual_password'")

def main():
    print("🗄️ ZAKIA Chatbot MySQL Connection Test")
    print("=" * 50)
    
    success = test_mysql_connection()
    
    if not success:
        show_config_help()
        print("\n🚀 After fixing the configuration, run:")
        print("   python test_mysql_connection.py")
        return False
    
    print("\n✅ MySQL connection is working perfectly!")
    print("🚀 You can now start the chatbot with:")
    print("   python start_chatbot.py")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)


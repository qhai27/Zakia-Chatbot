#!/usr/bin/env python3
"""
Database Setup Script for ZAKIA Chatbot
This script will initialize the database and insert FAQ data
"""

import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def main():
    print("ZAKIA Chatbot Database Setup")
    print("=" * 50)
    
    try:
        from database import DatabaseManager
        
        # Create database manager
        db = DatabaseManager()
        
        print("1. Creating database...")
        if not db.create_database():
            print("FAILED: Failed to create database")
            print("Please check your MySQL connection and credentials.")
            return False
        
        print("SUCCESS: Database created successfully")
        
        print("2. Connecting to database...")
        if not db.connect():
            print("FAILED: Failed to connect to database")
            print("Please check your MySQL connection and credentials.")
            return False
        
        print("SUCCESS: Connected to database")
        
        print("3. Creating tables...")
        if not db.create_tables():
            print("FAILED: Failed to create tables")
            return False
        
        print("SUCCESS: Tables created successfully")
        
        print("4. Inserting FAQ data...")
        if not db.insert_faqs():
            print("FAILED: Failed to insert FAQ data")
            return False
        
        print("SUCCESS: FAQ data inserted successfully")
        
        print("5. Testing FAQ retrieval...")
        faqs = db.get_faqs()
        if faqs:
            print(f"SUCCESS: Retrieved {len(faqs)} FAQs from database")
        else:
            print("FAILED: No FAQs found in database")
            return False
        
        # Close connection
        db.close()
        
        print("\nDatabase setup completed successfully!")
        print("You can now start the chatbot with: python start_chatbot.py")
        return True
        
    except ImportError as e:
        print(f"FAILED: Import Error: {e}")
        print("Please make sure you're in the correct directory and all dependencies are installed.")
        print("Run: pip install -r backend/requirement.txt")
        return False
        
    except Exception as e:
        print(f"FAILED: Error setting up database: {e}")
        print("Please check your MySQL connection and try again.")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("\nTroubleshooting Tips:")
        print("1. Make sure MySQL is running")
        print("2. Check your database credentials in backend/database.py")
        print("3. Verify the database 'lznk_chatbot' exists")
        print("4. Check your MySQL user permissions")
        sys.exit(1)

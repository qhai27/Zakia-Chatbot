#!/usr/bin/env python3
"""
Database initialization script for LZNK Chatbot
Run this script to set up the database and tables
"""

from database import DatabaseManager
import sys

def main():
    print("Initializing LZNK Chatbot Database...")
    
    # Create database manager
    db = DatabaseManager()
    
    # Step 1: Create database
    print("1. Creating database...")
    if not db.create_database():
        print("❌ Failed to create database")
        sys.exit(1)
    print("✅ Database created successfully")
    
    # Step 2: Connect to database
    print("2. Connecting to database...")
    if not db.connect():
        print("❌ Failed to connect to database")
        sys.exit(1)
    print("✅ Connected to database")
    
    # Step 3: Create tables
    print("3. Creating tables...")
    if not db.create_tables():
        print("❌ Failed to create tables")
        sys.exit(1)
    print("✅ Tables created successfully")
    
    # Step 4: Insert FAQ data
    print("4. Inserting FAQ data...")
    if not db.insert_faqs():
        print("❌ Failed to insert FAQ data")
        sys.exit(1)
    print("✅ FAQ data inserted successfully")
    
    # Close connection
    db.close()
    
    print("\n🎉 Database initialization completed successfully!")
    print("You can now run the Flask application with: python app.py")

if __name__ == "__main__":
    main()




"""
Database Diagnostic Script
Run this to check your database configuration
"""

import sys
import traceback

def check_imports():
    """Check if required packages are installed"""
    print("="*60)
    print("📦 CHECKING IMPORTS")
    print("="*60)
    
    required = {
        'mysql.connector': 'mysql-connector-python',
        'flask': 'flask',
        'flask_cors': 'flask-cors'
    }
    
    missing = []
    
    for module, package in required.items():
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} - Install with: pip install {package}")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️ Missing packages: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        return False
    
    print("\n✅ All required packages installed")
    return True


def check_database_config():
    """Check database configuration"""
    print("\n" + "="*60)
    print("🔧 CHECKING DATABASE CONFIGURATION")
    print("="*60)
    
    try:
        from database import DatabaseManager
        
        db = DatabaseManager()
        
        print(f"\nConfiguration:")
        print(f"  Host: {db.host}")
        print(f"  User: {db.user}")
        print(f"  Password: {'*' * len(db.password) if db.password else '(empty)'}")
        print(f"  Database: {db.database}")
        
        return db
    except Exception as e:
        print(f"\n❌ Error loading database configuration:")
        print(f"   {e}")
        traceback.print_exc()
        return None


def test_connection(db):
    """Test database connection"""
    print("\n" + "="*60)
    print("🔌 TESTING DATABASE CONNECTION")
    print("="*60)
    
    try:
        if db.connect():
            print("✅ Connected to MySQL successfully")
            
            # Get MySQL version
            cur = db.connection.cursor()
            cur.execute("SELECT VERSION()")
            version = cur.fetchone()[0]
            print(f"   MySQL Version: {version}")
            cur.close()
            
            return True
        else:
            print("❌ Failed to connect to MySQL")
            return False
            
    except Exception as e:
        print(f"❌ Connection error:")
        print(f"   {e}")
        traceback.print_exc()
        
        print("\n💡 Common fixes:")
        print("   1. Check MySQL is running:")
        print("      sudo systemctl status mysql")
        print("   2. Check credentials in backend/database.py")
        print("   3. Try connecting manually:")
        print(f"      mysql -u {db.user} -p")
        
        return False


def check_database_exists(db):
    """Check if target database exists"""
    print("\n" + "="*60)
    print("🗄️ CHECKING DATABASE")
    print("="*60)
    
    try:
        cur = db.connection.cursor()
        cur.execute("SHOW DATABASES")
        databases = [row[0] for row in cur.fetchall()]
        cur.close()
        
        print(f"\nAvailable databases: {', '.join(databases)}")
        
        if db.database in databases:
            print(f"✅ Database '{db.database}' exists")
            return True
        else:
            print(f"❌ Database '{db.database}' does NOT exist")
            print(f"\n💡 Create it with:")
            print(f"   mysql -u {db.user} -p")
            print(f"   CREATE DATABASE {db.database};")
            return False
            
    except Exception as e:
        print(f"❌ Error checking database:")
        print(f"   {e}")
        return False


def check_tables(db):
    """Check if required tables exist"""
    print("\n" + "="*60)
    print("📋 CHECKING TABLES")
    print("="*60)
    
    try:
        # Switch to target database
        db.connection.database = db.database
        
        cur = db.connection.cursor()
        cur.execute("SHOW TABLES")
        tables = [row[0] for row in cur.fetchall()]
        cur.close()
        
        required_tables = ['reminders', 'faqs', 'chat_logs', 'users']
        
        print(f"\nFound {len(tables)} tables:")
        for table in tables:
            print(f"  • {table}")
        
        print(f"\nRequired tables check:")
        all_exist = True
        for table in required_tables:
            if table in tables:
                print(f"  ✅ {table}")
            else:
                print(f"  ❌ {table} (missing)")
                all_exist = False
        
        return all_exist, tables
        
    except Exception as e:
        print(f"❌ Error checking tables:")
        print(f"   {e}")
        traceback.print_exc()
        return False, []


def check_reminders_table_structure(db):
    """Check reminders table structure"""
    print("\n" + "="*60)
    print("🔍 CHECKING REMINDERS TABLE STRUCTURE")
    print("="*60)
    
    try:
        cur = db.connection.cursor()
        cur.execute("DESCRIBE reminders")
        columns = cur.fetchall()
        cur.close()
        
        print("\nColumns:")
        required_columns = ['id', 'name', 'ic_number', 'phone', 'zakat_type', 
                          'zakat_amount', 'year', 'created_at', 'updated_at']
        
        found_columns = []
        for col in columns:
            col_name = col[0]
            col_type = col[1]
            col_null = "NULL" if col[2] == "YES" else "NOT NULL"
            found_columns.append(col_name)
            print(f"  • {col_name}: {col_type} {col_null}")
        
        print("\nRequired columns check:")
        all_present = True
        for req_col in required_columns:
            if req_col in found_columns:
                print(f"  ✅ {req_col}")
            else:
                print(f"  ❌ {req_col} (missing)")
                all_present = False
        
        return all_present
        
    except Exception as e:
        print(f"❌ Reminders table does not exist or error:")
        print(f"   {e}")
        return False


def test_insert(db):
    """Test inserting a record"""
    print("\n" + "="*60)
    print("✍️ TESTING INSERT")
    print("="*60)
    
    try:
        cur = db.connection.cursor()
        
        import datetime
        now = datetime.datetime.utcnow()
        
        sql = """
            INSERT INTO reminders 
            (name, ic_number, phone, zakat_type, zakat_amount, year, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            'Test User',
            '990101010101',
            '0123456789',
            'pendapatan',
            100.00,
            '2025 Masihi',
            now,
            now
        )
        
        print("\nInserting test record...")
        print(f"  Name: {values[0]}")
        print(f"  IC: {values[1]}")
        print(f"  Phone: {values[2]}")
        print(f"  Type: {values[3]}")
        
        cur.execute(sql, values)
        db.connection.commit()
        test_id = cur.lastrowid
        
        print(f"\n✅ Insert successful! ID: {test_id}")
        
        # Clean up
        print(f"\nCleaning up test record...")
        cur.execute("DELETE FROM reminders WHERE id = %s", (test_id,))
        db.connection.commit()
        cur.close()
        
        print("✅ Test record deleted")
        return True
        
    except Exception as e:
        print(f"\n❌ Insert failed:")
        print(f"   {e}")
        traceback.print_exc()
        
        # Try to rollback
        try:
            db.connection.rollback()
        except:
            pass
        
        return False


def main():
    """Run all diagnostics"""
    print("\n" + "="*60)
    print("🏥 DATABASE DIAGNOSTIC TOOL")
    print("="*60)
    
    # Step 1: Check imports
    if not check_imports():
        print("\n❌ Missing required packages. Please install them first.")
        return False
    
    # Step 2: Check database config
    db = check_database_config()
    if not db:
        print("\n❌ Database configuration error")
        return False
    
    # Step 3: Test connection
    if not test_connection(db):
        print("\n❌ Cannot connect to MySQL")
        return False
    
    # Step 4: Check database exists
    if not check_database_exists(db):
        print("\n❌ Target database does not exist")
        print(f"\n💡 Run this to create it:")
        print(f"   python -c \"from database import DatabaseManager; db = DatabaseManager(); db.create_database()\"")
        return False
    
    # Step 5: Check tables
    all_tables_exist, tables = check_tables(db)
    
    if 'reminders' not in tables:
        print("\n❌ Reminders table is missing")
        print("\n💡 Run this to create it:")
        print("   python backend/init_db.py")
        return False
    
    # Step 6: Check reminders table structure
    if not check_reminders_table_structure(db):
        print("\n❌ Reminders table structure is incorrect")
        print("\n💡 Run this to recreate it:")
        print("   DROP TABLE reminders;")
        print("   python backend/init_db.py")
        return False
    
    # Step 7: Test insert
    if not test_insert(db):
        print("\n❌ Cannot insert test record")
        return False
    
    # All checks passed
    print("\n" + "="*60)
    print("✅ ALL DIAGNOSTICS PASSED!")
    print("="*60)
    print("\n🎉 Your database is configured correctly!")
    print("\n📝 Next steps:")
    print("   1. Make sure Flask app is using the enhanced debug route")
    print("   2. Restart your Flask application")
    print("   3. Try saving a reminder again")
    print("   4. Check the server console for detailed logs")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)
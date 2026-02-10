"""
Admin Authentication Routes for ZAKIA Chatbot 
Handles login and signup 
"""

from flask import Blueprint, request, jsonify
from database import DatabaseManager
import traceback

# Create blueprint
admin_auth_bp = Blueprint('admin_auth', __name__, url_prefix='/admin/auth')

# Initialize database
db = DatabaseManager()

# ===============================================
# UTILITY FUNCTIONS
# ===============================================

def validate_admin_id(admin_id):
    """Validate admin ID format"""
    if not admin_id or len(admin_id) < 5:
        return False
    # Only lowercase letters and numbers
    return admin_id.isalnum() and admin_id.islower()

def validate_password(password):
    """Validate password strength"""
    if not password or len(password) < 8:
        return False, "Kata laluan mesti sekurang-kurangnya 8 aksara"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in '!@#$%^&*(),.?":{}|<>' for c in password)
    
    if not (has_upper and has_lower and has_digit and has_special):
        return False, "Kata laluan mesti mengandungi huruf besar, huruf kecil, nombor dan simbol"
    
    return True, ""

def ensure_admins_table():
    """Ensure admins table exists and column is updated"""
    try:
        # Create new connection for table creation
        temp_db = DatabaseManager()
        if not temp_db.connect():
            print("❌ Failed to connect for table creation")
            return False
        
        cursor = temp_db.connection.cursor()
        
        # Create admins table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INT AUTO_INCREMENT PRIMARY KEY,
                admin_id VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """)
        
        # Migrate password_hash column to password if needed
        try:
            cursor.execute("ALTER TABLE admins CHANGE COLUMN password_hash password VARCHAR(255) NOT NULL")
            print("✅ Migrated password_hash column to password")
        except Exception as e:
            if "1054" not in str(e) and "Unknown column" not in str(e):
                # Column might already exist or be named 'password', this is okay
                pass
        
        temp_db.connection.commit()
        cursor.close()
        temp_db.close()
        
        print("✅ Admins table verified and updated")
        return True
        
    except Exception as e:
        print(f"❌ Error creating admins table: {e}")
        return False

# ===============================================
# SIGNUP ROUTE
# ===============================================

@admin_auth_bp.route('/signup', methods=['POST', 'OPTIONS'])
def signup():
    """Register new admin account"""
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        print("\n" + "="*50)
        print("📝 SIGNUP REQUEST RECEIVED")
        print("="*50)
        
        # Get request data
        data = request.get_json(force=True) or {}
        
        name = (data.get('name') or '').strip()
        admin_id = (data.get('adminId') or '').strip().lower()
        email = (data.get('email') or '').strip().lower()
        password = data.get('password') or ''
        
        print(f"👤 Name: {name}")
        print(f"🆔 Admin ID: {admin_id}")
        print(f"📧 Email: {email}")
        
        # Validation
        if not name:
            return jsonify({'success': False, 'error': 'Nama penuh diperlukan'}), 400
        
        if not admin_id:
            return jsonify({'success': False, 'error': 'ID pentadbir diperlukan'}), 400
        
        if not validate_admin_id(admin_id):
            return jsonify({
                'success': False,
                'error': 'ID pentadbir tidak sah. Gunakan huruf kecil dan nombor sahaja (min. 5 aksara)'
            }), 400
        
        if not email or '@' not in email:
            return jsonify({'success': False, 'error': 'E-mel tidak sah'}), 400
        
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400
        
        print("✅ All validations passed")
        
        # Ensure table exists
        ensure_admins_table()
        
        # Create fresh connection for this request
        signup_db = DatabaseManager()
        if not signup_db.connect():
            return jsonify({'success': False, 'error': 'Ralat sambungan pangkalan data'}), 500
        
        try:
            cursor = signup_db.connection.cursor(dictionary=True)
            
            # Check if admin_id exists
            cursor.execute("SELECT id FROM admins WHERE admin_id = %s", (admin_id,))
            if cursor.fetchone():
                cursor.close()
                signup_db.close()
                return jsonify({'success': False, 'error': 'ID pentadbir sudah digunakan'}), 400
            
            # Check if email exists
            cursor.execute("SELECT id FROM admins WHERE email = %s", (email,))
            if cursor.fetchone():
                cursor.close()
                signup_db.close()
                return jsonify({'success': False, 'error': 'E-mel sudah didaftarkan'}), 400
            
            # Store password as plain text
            cursor.execute("""
                INSERT INTO admins (admin_id, name, email, password)
                VALUES (%s, %s, %s, %s)
            """, (admin_id, name, email, password))
            
            signup_db.connection.commit()
            cursor.close()
            signup_db.close()
            
            print(f"✅ Admin registered: {admin_id}")
            print("="*50 + "\n")
            
            return jsonify({
                'success': True,
                'message': 'Akaun berjaya didaftarkan',
                'admin_id': admin_id,
                'name': name
            }), 201
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            if signup_db.connection:
                signup_db.connection.rollback()
            signup_db.close()
            raise
        
    except Exception as e:
        print(f"❌ SIGNUP ERROR: {e}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': 'Ralat sistem'}), 500

# ===============================================
# LOGIN ROUTE
# ===============================================

@admin_auth_bp.route('/login', methods=['POST', 'OPTIONS'])
def login():
    """Authenticate admin"""
    
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        print("\n" + "="*50)
        print("🔐 LOGIN REQUEST")
        print("="*50)
        
        data = request.get_json(force=True) or {}
        admin_id = (data.get('adminId') or '').strip().lower()
        password = data.get('password') or ''
        
        if not admin_id or not password:
            return jsonify({'success': False, 'error': 'Sila masukkan ID dan kata laluan'}), 400
        
        # Create fresh connection
        login_db = DatabaseManager()
        if not login_db.connect():
            return jsonify({'success': False, 'error': 'Ralat sambungan'}), 500
        
        try:
            cursor = login_db.connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT id, admin_id, name, email, password
                FROM admins
                WHERE admin_id = %s
            """, (admin_id,))
            
            admin = cursor.fetchone()
            cursor.close()
            login_db.close()
            
            if not admin:
                print("❌ Admin not found")
                return jsonify({'success': False, 'error': 'ID atau kata laluan tidak sah'}), 401
            
            # Verify password (direct comparison)
            if password != admin['password']:
                print("❌ Invalid password")
                return jsonify({'success': False, 'error': 'ID atau kata laluan tidak sah'}), 401
            
            print(f"✅ Login successful: {admin['name']}")
            print("="*50 + "\n")
            
            return jsonify({
                'success': True,
                'message': 'Log masuk berjaya',
                'admin_id': admin['admin_id'],
                'name': admin['name'],
                'email': admin['email']
            })
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            login_db.close()
            raise
        
    except Exception as e:
        print(f"❌ LOGIN ERROR: {e}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': 'Ralat sistem'}), 500

# ===============================================
# LOGOUT ROUTE
# ===============================================

@admin_auth_bp.route('/logout', methods=['POST', 'OPTIONS'])
def logout():
    """Logout admin"""
    if request.method == 'OPTIONS':
        return '', 204
    
    return jsonify({'success': True, 'message': 'Log keluar berjaya'})

# ===============================================
# HEALTH CHECK
# ===============================================

@admin_auth_bp.route('/health', methods=['GET'])
def health_check():
    """Health check"""
    try:
        test_db = DatabaseManager()
        if test_db.connect():
            cursor = test_db.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM admins")
            count = cursor.fetchone()[0]
            cursor.close()
            test_db.close()
            
            return jsonify({
                'success': True,
                'message': 'Endpoints operational',
                'database': 'connected',
                'admin_count': count
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Database connection failed',
                'database': 'disconnected'
            }), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_auth_bp.route('/test-db', methods=['GET'])
def test_database():
    """Test database"""
    try:
        test_db = DatabaseManager()
        connected = test_db.connect()
        
        if connected:
            ensure_admins_table()
            cursor = test_db.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM admins")
            count = cursor.fetchone()[0]
            cursor.close()
            test_db.close()
            
            return jsonify({
                'success': True,
                'results': {
                    'connection': True,
                    'tables_created': True,
                    'admin_count': count
                }
            })
        else:
            return jsonify({
                'success': False,
                'results': {
                    'connection': False,
                    'tables_created': False,
                    'admin_count': 0
                }
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500
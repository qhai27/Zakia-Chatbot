"""
Admin Authentication Routes for ZAKIA Chatbot
Handles login, signup, and session management
"""

from flask import Blueprint, request, jsonify
from database import DatabaseManager
import hashlib
import secrets
import datetime

# Create blueprint
admin_auth_bp = Blueprint('admin_auth', __name__, url_prefix='/admin/auth')

# Initialize database
db = DatabaseManager()

# ===============================================
# UTILITY FUNCTIONS
# ===============================================

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def generate_token():
    """Generate secure authentication token"""
    return secrets.token_urlsafe(32)

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

# ===============================================
# DATABASE SETUP
# ===============================================

def create_admin_tables():
    """Create admin users table if not exists"""
    try:
        if not db.connection or not db.connection.is_connected():
            db.connect()
        
        cursor = db.connection.cursor()
        
        # Create admins table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INT AUTO_INCREMENT PRIMARY KEY,
                admin_id VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(64) NOT NULL,
                token VARCHAR(64),
                token_expiry DATETIME,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP NULL,
                is_active TINYINT(1) DEFAULT 1,
                INDEX idx_admin_id (admin_id),
                INDEX idx_email (email),
                INDEX idx_token (token)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        db.connection.commit()
        cursor.close()
        
        print("✅ Admin tables created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin tables: {e}")
        if db.connection:
            db.connection.rollback()
        return False

# ===============================================
# SIGNUP ROUTE
# ===============================================

@admin_auth_bp.route('/signup', methods=['POST'])
def signup():
    """Register new admin account"""
    try:
        # Get request data
        data = request.get_json(force=True) or {}
        
        name = (data.get('name') or '').strip()
        admin_id = (data.get('adminId') or '').strip().lower()
        email = (data.get('email') or '').strip().lower()
        password = data.get('password') or ''
        
        # Validation
        if not name:
            return jsonify({
                'success': False,
                'error': 'Nama penuh diperlukan'
            }), 400
        
        if not admin_id:
            return jsonify({
                'success': False,
                'error': 'ID pentadbir diperlukan'
            }), 400
        
        if not validate_admin_id(admin_id):
            return jsonify({
                'success': False,
                'error': 'ID pentadbir tidak sah. Gunakan huruf kecil dan nombor sahaja (min. 5 aksara)'
            }), 400
        
        if not email:
            return jsonify({
                'success': False,
                'error': 'E-mel diperlukan'
            }), 400
        
        if '@' not in email:
            return jsonify({
                'success': False,
                'error': 'Format e-mel tidak sah'
            }), 400
        
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # Ensure database connection
        if not db.connection or not db.connection.is_connected():
            db.connect()
        
        # Ensure tables exist
        create_admin_tables()
        
        cursor = db.connection.cursor(dictionary=True)
        
        # Check if admin_id already exists
        cursor.execute("SELECT id FROM admins WHERE admin_id = %s", (admin_id,))
        if cursor.fetchone():
            cursor.close()
            return jsonify({
                'success': False,
                'error': 'ID pentadbir sudah digunakan'
            }), 400
        
        # Check if email already exists
        cursor.execute("SELECT id FROM admins WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            return jsonify({
                'success': False,
                'error': 'E-mel sudah didaftarkan'
            }), 400
        
        # Hash password
        password_hash = hash_password(password)
        
        # Insert new admin
        cursor.execute("""
            INSERT INTO admins (admin_id, name, email, password_hash)
            VALUES (%s, %s, %s, %s)
        """, (admin_id, name, email, password_hash))
        
        db.connection.commit()
        new_id = cursor.lastrowid
        cursor.close()
        
        print(f"✅ New admin registered: {admin_id} (ID: {new_id})")
        
        return jsonify({
            'success': True,
            'message': 'Akaun berjaya didaftarkan',
            'admin_id': admin_id
        })
        
    except Exception as e:
        print(f"❌ Signup error: {e}")
        if db.connection:
            db.connection.rollback()
        
        return jsonify({
            'success': False,
            'error': 'Ralat sistem. Sila cuba lagi.'
        }), 500

# ===============================================
# LOGIN ROUTE
# ===============================================

@admin_auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate admin and generate session token"""
    try:
        # Get request data
        data = request.get_json(force=True) or {}
        
        admin_id = (data.get('adminId') or '').strip().lower()
        password = data.get('password') or ''
        remember_me = data.get('rememberMe', False)
        
        # Validation
        if not admin_id or not password:
            return jsonify({
                'success': False,
                'error': 'ID pentadbir dan kata laluan diperlukan'
            }), 400
        
        # Ensure database connection
        if not db.connection or not db.connection.is_connected():
            db.connect()
        
        # Ensure tables exist
        create_admin_tables()
        
        cursor = db.connection.cursor(dictionary=True)
        
        # Get admin by admin_id
        cursor.execute("""
            SELECT id, admin_id, name, email, password_hash, is_active
            FROM admins
            WHERE admin_id = %s
        """, (admin_id,))
        
        admin = cursor.fetchone()
        
        if not admin:
            cursor.close()
            return jsonify({
                'success': False,
                'error': 'ID pentadbir atau kata laluan tidak sah'
            }), 401
        
        # Check if account is active
        if not admin['is_active']:
            cursor.close()
            return jsonify({
                'success': False,
                'error': 'Akaun tidak aktif. Sila hubungi pentadbir sistem.'
            }), 403
        
        # Verify password
        password_hash = hash_password(password)
        
        if password_hash != admin['password_hash']:
            cursor.close()
            return jsonify({
                'success': False,
                'error': 'ID pentadbir atau kata laluan tidak sah'
            }), 401
        
        # Generate authentication token
        token = generate_token()
        
        # Set token expiry (30 days if remember_me, otherwise 1 day)
        expiry_days = 30 if remember_me else 1
        token_expiry = datetime.datetime.now() + datetime.timedelta(days=expiry_days)
        
        # Update admin record with token
        cursor.execute("""
            UPDATE admins
            SET token = %s,
                token_expiry = %s,
                last_login = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (token, token_expiry, admin['id']))
        
        db.connection.commit()
        cursor.close()
        
        print(f"✅ Admin logged in: {admin_id}")
        
        return jsonify({
            'success': True,
            'message': 'Log masuk berjaya',
            'token': token,
            'admin_id': admin['admin_id'],
            'name': admin['name'],
            'email': admin['email']
        })
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        if db.connection:
            db.connection.rollback()
        
        return jsonify({
            'success': False,
            'error': 'Ralat sistem. Sila cuba lagi.'
        }), 500

# ===============================================
# VERIFY TOKEN ROUTE
# ===============================================

@admin_auth_bp.route('/verify', methods=['POST'])
def verify_token():
    """Verify authentication token"""
    try:
        # Get token from request
        data = request.get_json(force=True) or {}
        token = data.get('token')
        
        if not token:
            return jsonify({
                'success': False,
                'error': 'Token diperlukan'
            }), 400
        
        # Ensure database connection
        if not db.connection or not db.connection.is_connected():
            db.connect()
        
        cursor = db.connection.cursor(dictionary=True)
        
        # Get admin by token
        cursor.execute("""
            SELECT id, admin_id, name, email, token_expiry
            FROM admins
            WHERE token = %s AND is_active = 1
        """, (token,))
        
        admin = cursor.fetchone()
        cursor.close()
        
        if not admin:
            return jsonify({
                'success': False,
                'error': 'Token tidak sah'
            }), 401
        
        # Check token expiry
        if admin['token_expiry'] < datetime.datetime.now():
            return jsonify({
                'success': False,
                'error': 'Token tamat tempoh. Sila log masuk semula.'
            }), 401
        
        return jsonify({
            'success': True,
            'admin_id': admin['admin_id'],
            'name': admin['name'],
            'email': admin['email']
        })
        
    except Exception as e:
        print(f"❌ Verify token error: {e}")
        return jsonify({
            'success': False,
            'error': 'Ralat sistem'
        }), 500

# ===============================================
# LOGOUT ROUTE
# ===============================================

@admin_auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout admin and invalidate token"""
    try:
        # Get token from request
        data = request.get_json(force=True) or {}
        token = data.get('token')
        
        if not token:
            return jsonify({
                'success': False,
                'error': 'Token diperlukan'
            }), 400
        
        # Ensure database connection
        if not db.connection or not db.connection.is_connected():
            db.connect()
        
        cursor = db.connection.cursor()
        
        # Clear token
        cursor.execute("""
            UPDATE admins
            SET token = NULL, token_expiry = NULL
            WHERE token = %s
        """, (token,))
        
        db.connection.commit()
        cursor.close()
        
        print("✅ Admin logged out")
        
        return jsonify({
            'success': True,
            'message': 'Log keluar berjaya'
        })
        
    except Exception as e:
        print(f"❌ Logout error: {e}")
        return jsonify({
            'success': False,
            'error': 'Ralat sistem'
        }), 500

# ===============================================
# HEALTH CHECK
# ===============================================

@admin_auth_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for authentication endpoints"""
    return jsonify({
        'success': True,
        'message': 'Authentication endpoints operational'
    })
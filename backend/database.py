import mysql.connector
from mysql.connector import Error, pooling
import json
from datetime import datetime
import time


class DatabaseManager:
    # Class-level connection pool
    _pool = None
    _pool_name = "lznk_pool"

    def __init__(self, host=None, user=None, password=None, database=None):
        self.host = host or 'localhost'
        self.user = user or 'root'
        self.password = password or ''       
        self.database = database or 'lznk_chatbot'
        self.connection = None
        self.max_retries = 3
        self.retry_delay = 2

        # Create pool only once
        if DatabaseManager._pool is None:
            self._init_pool()

    # -----------------------------------------------------------
    # INITIALIZE POOL 
    # -----------------------------------------------------------
    def _init_pool(self):
        """Initialize connection pool with retry logic"""
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                DatabaseManager._pool = pooling.MySQLConnectionPool(
                    pool_name=self._pool_name,
                    pool_size=5,
                    pool_reset_session=True,
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    autocommit=False,
                    connect_timeout=10,
                    charset='utf8mb4',
                    collation='utf8mb4_general_ci',
                    raise_on_warnings=False
                )
                print("✅ Connection pool initialized")
                return True
            except Error as e:
                retry_count += 1
                print(f"⚠️ Pool creation attempt {retry_count}/{self.max_retries} failed: {e}")
                if retry_count < self.max_retries:
                    time.sleep(self.retry_delay)
                else:
                    print(f"❌ Could not create connection pool after {self.max_retries} attempts")
                    DatabaseManager._pool = None
                    return False

    # -----------------------------------------------------------
    # CONNECT FUNCTION 
    # -----------------------------------------------------------
    def connect(self):
        """Get connection from pool or fallback to direct connection with retry logic."""
        retry_count = 0
        
        while retry_count < self.max_retries:
            # 1) Try pool first
            try:
                if DatabaseManager._pool is not None:
                    self.connection = DatabaseManager._pool.get_connection()
                    if self.connection.is_connected():
                        print(f"✅ Connection obtained from pool (attempt {retry_count + 1})")
                        return True
            except Exception as e:
                print(f"⚠️ Pool connection failed (attempt {retry_count + 1}): {e}")

            # 2) Fallback to direct connection
            try:
                self.connection = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    autocommit=False,
                    connect_timeout=10,
                    charset='utf8mb4',
                    collation='utf8mb4_general_ci',
                    use_pure=True,
                    raise_on_warnings=False
                )

                if self.connection.is_connected():
                    print(f"✅ Direct MySQL connection established (attempt {retry_count + 1})")
                    return True

            except Error as e:
                retry_count += 1
                print(f"❌ MySQL Connection Error (attempt {retry_count}/{self.max_retries}): {e}")
                
                if retry_count < self.max_retries:
                    print(f"   Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    print("❌ All connection attempts failed")
                    self.connection = None
                    return False

        return False

    # -----------------------------------------------------------
    # ENSURE CONNECTION
    # -----------------------------------------------------------
    def ensure_connection(self):
        """Ensure connection is alive with enhanced retry logic"""
        try:
            if self.connection is None or not self.connection.is_connected():
                print("⚠️ MySQL connection lost, reconnecting...")
                return self.connect()

            # Try to ping the connection
            try:
                self.connection.ping(reconnect=True, attempts=3, delay=1)
                return True
            except Error as ping_error:
                print(f"⚠️ Ping failed: {ping_error}, reconnecting...")
                return self.connect()

        except Exception as e:
            print(f"⚠️ Connection check error: {e}, reconnecting...")
            return self.connect()

    # -----------------------------------------------------------
    # CREATE DATABASE 
    # -----------------------------------------------------------
    def create_database(self):
        """Create database if not exists with retry logic"""
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                conn = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    autocommit=True,
                    connect_timeout=10
                )
                cursor = conn.cursor()
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS {self.database} "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci"
                )
                cursor.close()
                conn.close()
                print(f"✅ Database '{self.database}' is ready")
                return True
                
            except Error as e:
                retry_count += 1
                print(f"❌ Database creation error (attempt {retry_count}/{self.max_retries}): {e}")
                
                if retry_count < self.max_retries:
                    time.sleep(self.retry_delay)
                else:
                    return False

    # -----------------------------------------------------------
    # CREATE TABLES
    # -----------------------------------------------------------
    def create_tables(self):
        if not self.ensure_connection():
            return False

        try:
            cursor = self.connection.cursor()

            # FAQs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS faqs (
                    id_faq INT AUTO_INCREMENT PRIMARY KEY,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    category VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_category (category)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            # Users Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id_user INT AUTO_INCREMENT PRIMARY KEY,
                    session_id VARCHAR(100) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_last_activity (last_activity),
                    INDEX idx_created_at (created_at),
                    INDEX idx_session_id (session_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            # Chat Logs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_logs (
                    id_log INT AUTO_INCREMENT PRIMARY KEY,
                    id_user INT,
                    user_message TEXT NOT NULL,
                    bot_response TEXT NOT NULL,
                    session_id VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_session (session_id),
                    INDEX idx_created (created_at),
                    INDEX idx_id_user (id_user),
                    INDEX idx_user_created (id_user, created_at),
                    INDEX idx_session_created (session_id, created_at),
                    FOREIGN KEY (id_user) REFERENCES users(id_user) ON DELETE SET NULL ON UPDATE CASCADE,
                    FOREIGN KEY (session_id) REFERENCES users(session_id) ON DELETE SET NULL ON UPDATE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            # ===== NEW: Contact Requests Table (replaces live_chat_requests) =====
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contact_requests (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id VARCHAR(255),
                    
                    -- User information
                    name VARCHAR(255) NOT NULL,
                    phone VARCHAR(20) NOT NULL,
                    email VARCHAR(255),
                    
                    -- Request details
                    question TEXT NOT NULL,
                    preferred_contact_method ENUM('whatsapp', 'phone', 'email') DEFAULT 'whatsapp',
                    
                    -- Context
                    conversation_history TEXT,
                    trigger_type VARCHAR(50),
                    
                    -- Status tracking
                    status ENUM('pending', 'contacted', 'resolved') DEFAULT 'pending',
                    priority ENUM('normal', 'urgent') DEFAULT 'normal',
                    
                    -- Admin response
                    admin_notes TEXT,
                    contacted_by VARCHAR(100),
                    contacted_at TIMESTAMP NULL,
                    contact_method_used VARCHAR(50),
                    
                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    
                    -- Indexes
                    INDEX idx_session (session_id),
                    INDEX idx_status (status),
                    INDEX idx_created (created_at),
                    INDEX idx_phone (phone),
                    INDEX idx_priority (priority, status)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("✅ Contact requests table created/verified")

            # Keep old live_chat_requests for backward compatibility (optional)
            # You can comment this out after migration
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS live_chat_requests (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id VARCHAR(100),
                    user_message TEXT NOT NULL,
                    bot_response TEXT,
                    status ENUM('open', 'in_progress', 'resolved') DEFAULT 'open',
                    admin_response TEXT,
                    admin_name VARCHAR(100),
                    is_delivered TINYINT(1) DEFAULT 0,
                    delivered_at TIMESTAMP NULL DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_status (status),
                    INDEX idx_created (created_at),
                    INDEX idx_session (session_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            # Migration: ensure new columns exist on older databases
            try:
                cursor.execute("""
                    ALTER TABLE live_chat_requests
                    ADD COLUMN is_delivered TINYINT(1) DEFAULT 0,
                    ADD COLUMN delivered_at TIMESTAMP NULL DEFAULT NULL
                """)
            except Error as e:
                if "Duplicate column" not in str(e) and "1060" not in str(e):
                    print(f"⚠️ Could not migrate live_chat_requests columns: {e}")

            self.connection.commit()
            cursor.close()
            
            # Add foreign keys to existing tables if they don't exist
            self.add_foreign_keys()
            
            print("✅ All tables are ready")
            return True

        except Error as e:
            print(f"❌ Table creation error: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    # -----------------------------------------------------------
    # MIGRATION: Live Chat to Contact Requests (Optional Helper)
    # -----------------------------------------------------------
    def migrate_live_chat_to_contact_requests(self):
        """
        Migrate existing live_chat_requests to contact_requests table.
        Call this once if you have existing data.
        """
        if not self.ensure_connection():
            return False
        
        try:
            cursor = self.connection.cursor()
            
            print("🔄 Migrating live_chat_requests to contact_requests...")
            
            # Check if there's data to migrate
            cursor.execute("SELECT COUNT(*) FROM live_chat_requests")
            count = cursor.fetchone()[0]
            
            if count == 0:
                print("ℹ️ No live chat requests to migrate")
                cursor.close()
                return True
            
            # Migrate data
            cursor.execute("""
                INSERT INTO contact_requests 
                (session_id, name, phone, question, status, admin_notes, contacted_at, created_at)
                SELECT 
                    session_id,
                    'Legacy User' as name,
                    'N/A' as phone,
                    user_message as question,
                    CASE 
                        WHEN status = 'resolved' THEN 'contacted'
                        WHEN status = 'in_progress' THEN 'pending'
                        ELSE status 
                    END as status,
                    CONCAT('Bot response: ', COALESCE(bot_response, ''), 
                           '\nAdmin response: ', COALESCE(admin_response, '')) as admin_notes,
                    updated_at as contacted_at,
                    created_at
                FROM live_chat_requests
                WHERE user_message IS NOT NULL
                AND id NOT IN (
                    SELECT id FROM contact_requests WHERE id IS NOT NULL
                )
            """)
            
            migrated = cursor.rowcount
            self.connection.commit()
            cursor.close()
            
            print(f"✅ Migrated {migrated} records from live_chat_requests to contact_requests")
            return True
            
        except Error as e:
            print(f"❌ Migration error: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    # -----------------------------------------------------------
    # ADD FOREIGN KEYS (MIGRATION)
    # -----------------------------------------------------------
    def add_foreign_keys(self):
        """Add foreign key constraints to existing tables if they don't exist"""
        if not self.ensure_connection():
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # Check if foreign keys already exist and add them if not
            # For chat_logs.id_user -> users.id_user
            try:
                cursor.execute("""
                    SELECT CONSTRAINT_NAME 
                    FROM information_schema.KEY_COLUMN_USAGE 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'chat_logs' 
                    AND COLUMN_NAME = 'id_user' 
                    AND REFERENCED_TABLE_NAME = 'users'
                """)
                if not cursor.fetchone():
                    # Add id_user column if it doesn't exist
                    try:
                        cursor.execute("ALTER TABLE chat_logs ADD COLUMN id_user INT NULL AFTER id_log")
                        cursor.execute("ALTER TABLE chat_logs ADD INDEX idx_id_user (id_user)")
                    except Error as e:
                        if "Duplicate column name" not in str(e):
                            print(f"⚠️ Could not add id_user column: {e}")
                    
                    # Add foreign key
                    try:
                        cursor.execute("""
                            ALTER TABLE chat_logs 
                            ADD CONSTRAINT fk_chat_logs_id_user 
                            FOREIGN KEY (id_user) REFERENCES users(id_user) 
                            ON DELETE SET NULL ON UPDATE CASCADE
                        """)
                        print("✅ Added foreign key: chat_logs.id_user -> users.id_user")
                    except Error as e:
                        if "Duplicate foreign key" not in str(e) and "already exists" not in str(e):
                            print(f"⚠️ Could not add foreign key for id_user: {e}")
            except Error as e:
                print(f"⚠️ Error checking/adding id_user foreign key: {e}")
            
            # For chat_logs.session_id -> users.session_id
            try:
                cursor.execute("""
                    SELECT CONSTRAINT_NAME 
                    FROM information_schema.KEY_COLUMN_USAGE 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'chat_logs' 
                    AND COLUMN_NAME = 'session_id' 
                    AND REFERENCED_TABLE_NAME = 'users'
                """)
                if not cursor.fetchone():
                    # Migrate existing session_ids to users table
                    print("📝 Migrating existing session_ids to users table...")
                    cursor.execute("""
                        INSERT INTO users (session_id, created_at, last_activity)
                        SELECT DISTINCT session_id, MIN(created_at), MAX(created_at)
                        FROM chat_logs
                        WHERE session_id IS NOT NULL
                        AND session_id NOT IN (SELECT session_id FROM users WHERE session_id IS NOT NULL)
                        GROUP BY session_id
                    """)
                    migrated_count = cursor.rowcount
                    if migrated_count > 0:
                        print(f"✅ Created {migrated_count} users from existing chat_logs")
                    
                    # Update id_user in chat_logs for the newly created users
                    cursor.execute("""
                        UPDATE chat_logs cl
                        INNER JOIN users u ON cl.session_id = u.session_id
                        SET cl.id_user = u.id_user
                        WHERE cl.id_user IS NULL
                    """)
                    updated_count = cursor.rowcount
                    if updated_count > 0:
                        print(f"✅ Updated {updated_count} chat_logs with user_id")
                    
                    self.connection.commit()
                    
                    # Now add the foreign key
                    cursor.execute("""
                        ALTER TABLE chat_logs 
                        ADD CONSTRAINT fk_chat_logs_session_id 
                        FOREIGN KEY (session_id) REFERENCES users(session_id) 
                        ON DELETE SET NULL ON UPDATE CASCADE
                    """)
                    print("✅ Added foreign key: chat_logs.session_id -> users.session_id")
            except Error as e:
                if "Duplicate foreign key" not in str(e) and "already exists" not in str(e):
                    print(f"⚠️ Could not add foreign key for session_id: {e}")
                    if "1452" in str(e) or "Cannot add or update" in str(e):
                        print("   ℹ️ Some session_ids in chat_logs may not have corresponding users")
                        print("   ℹ️ You may need to clean up orphaned session_ids first")
            
            self.connection.commit()
            cursor.close()
            return True
            
        except Error as e:
            print(f"⚠️ Foreign key migration error: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    # -----------------------------------------------------------
    # INSERT FAQ
    # -----------------------------------------------------------
    def insert_faqs(self):
        if not self.ensure_connection():
            return False

        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM faqs")
            count = cursor.fetchone()[0]

            if count > 0:
                print("ℹ️ FAQs already exist, skipping.")
                cursor.close()
                return True

            faqs = [
                ("Apa itu zakat?", "Zakat ialah kewajipan agama Islam untuk mengeluarkan sebahagian harta tertentu kepada golongan yang berhak menerimanya. Ia adalah rukun Islam yang ketiga dan wajib ke atas setiap Muslim yang memenuhi syarat tertentu. 💰", "Umum"),
                ("Siapa yang wajib membayar zakat?", "Setiap Muslim yang berakal, baligh, merdeka dan memiliki harta yang mencapai nisab serta cukup haul (tempoh setahun) wajib mengeluarkan zakat. 😊", "Umum"),
                ("Bagaimana cara membayar zakat?", "Anda boleh membayar zakat melalui portal online LZNK, kaunter pejabat LZNK, atau melalui potongan gaji. Bayaran boleh dibuat secara tunai, kad kredit/debit, atau FPX. 💳", "Pembayaran"),
                ("Apakah waktu sesuai untuk bayar zakat?", "Zakat wajib dibayar sebaik sahaja cukup haul (setahun) dan mencapai nisab. Namun, lebih afdal dibayar pada bulan Ramadan kerana pahalanya berganda. 📅", "Pembayaran"),
                ("Berapakah nisab zakat emas?", "Nisab zakat emas ialah 85 gram emas. Jika anda memiliki emas seberat 85 gram atau lebih dan telah dimiliki selama setahun, anda wajib mengeluarkan zakat sebanyak 2.5%. ⚖️", "Nisab"),
                ("Berapakah kadar zakat emas?", "Kadar zakat emas ialah 2.5% daripada jumlah emas yang dimiliki. Contoh: Jika anda ada 100 gram emas, zakat yang perlu dibayar ialah 2.5 gram emas atau nilai setara dalam wang. 💰", "Kadar"),
                ("Bagaimana mengira zakat perniagaan?", "Zakat perniagaan dikira 2.5% daripada (Modal + Untung + Wang Tunai + Aset Semasa) - (Hutang Perniagaan). Haul dikira dari tarikh mula perniagaan mencapai nisab. 📊", "Perniagaan"),
                ("Bilakah haul zakat bermula?", "Haul bermula apabila harta anda mula mencapai nisab dan dikira genap 12 bulan Hijrah (354 hari) atau 12 bulan Masihi (365 hari). Jika harta kurang dari nisab dalam tempoh tersebut, haul bermula semula. 📆", "Haul"),
                ("Apa itu LZNK?", "LZNK adalah Lembaga Zakat Negeri Kedah, institusi yang bertanggungjawab mengutip dan mengagih zakat di negeri Kedah mengikut hukum syarak. LZNK ditubuhkan untuk memastikan zakat disalurkan kepada golongan yang berhak. 🏢", "LZNK"),
                ("Di mana lokasi pejabat LZNK?", "Pejabat utama LZNK terletak di Wisma Persatuan, Jalan Teluk Wan Jah, 05400 Alor Setar, Kedah. Kami juga mempunyai beberapa kaunter cawangan di seluruh negeri Kedah. Hubungi 04-733 6633 untuk maklumat lanjut. 📍", "LZNK"),
            ]

            cursor.executemany("""
                INSERT INTO faqs (question, answer, category)
                VALUES (%s, %s, %s)
            """, faqs)

            self.connection.commit()
            cursor.close()
            print(f"✅ {len(faqs)} FAQ inserted successfully")
            return True

        except Error as e:
            print(f"❌ FAQ insert error: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    # [REST OF THE METHODS REMAIN THE SAME - truncated for brevity]
    # Including: CRUD FAQ, USER MANAGEMENT, LOG CHAT, etc.
    
    def get_faqs(self):
        if not self.ensure_connection():
            return []
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM faqs ORDER BY category, question")
            data = cursor.fetchall()
            cursor.close()
            return data
        except Error as e:
            print(f"❌ FAQ fetch error: {e}")
            return []

    def get_faq_by_id(self, faq_id):
        if not self.ensure_connection():
            return None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM faqs WHERE id_faq = %s", (faq_id,))
            faq = cursor.fetchone()
            cursor.close()
            return faq
        except Error as e:
            print(f"❌ FAQ fetch by ID error: {e}")
            return None

    def create_faq(self, q, a, c=None):
        if not self.ensure_connection():
            return None
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO faqs (question, answer, category) VALUES (%s, %s, %s)",
                (q, a, c)
            )
            self.connection.commit()
            new_id = cursor.lastrowid
            cursor.close()
            return new_id
        except Error as e:
            print(f"❌ FAQ create error: {e}")
            if self.connection:
                self.connection.rollback()
            return None

    def update_faq(self, faq_id, q, a, c=None):
        if not self.ensure_connection():
            return False
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE faqs SET question=%s, answer=%s, category=%s
                WHERE id_faq=%s
            """, (q, a, c, faq_id))
            self.connection.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0
        except Error as e:
            print(f"❌ FAQ update error: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    def delete_faq(self, faq_id):
        if not self.ensure_connection():
            return False
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM faqs WHERE id_faq=%s", (faq_id,))
            self.connection.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0
        except Error as e:
            print(f"❌ FAQ delete error: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    # USER MANAGEMENT
    def get_or_create_user(self, session_id):
        """Get or create a user by session_id."""
        if not session_id:
            return None
            
        if not self.ensure_connection():
            print("⚠️ Cannot get/create user - no database connection")
            return None
            
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("SELECT id_user FROM users WHERE session_id = %s", (session_id,))
            user_result = cursor.fetchone()
            
            if user_result:
                user_id = user_result[0]
                cursor.execute("""
                    UPDATE users 
                    SET last_activity = CURRENT_TIMESTAMP 
                    WHERE id_user = %s
                """, (user_id,))
                self.connection.commit()
                cursor.close()
                return user_id
            else:
                cursor.execute("""
                    INSERT INTO users (session_id, created_at, last_activity)
                    VALUES (%s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (session_id,))
                user_id = cursor.lastrowid
                self.connection.commit()
                cursor.close()
                print(f"✅ Created new user with session_id: {session_id[:8]}... (id: {user_id})")
                return user_id
                
        except Error as e:
            print(f"❌ Error getting/creating user: {e}")
            if self.connection:
                self.connection.rollback()
            return None

    def log_chat(self, user_message, bot_response, session_id=None):
        if not self.ensure_connection():
            print("⚠️ Cannot log chat - no database connection")
            return False
        try:
            cursor = self.connection.cursor()
            
            user_id = None
            if session_id:
                user_id = self.get_or_create_user(session_id)
            
            cursor.execute("""
                INSERT INTO chat_logs (id_user, user_message, bot_response, session_id)
                VALUES (%s, %s, %s, %s)
            """, (user_id, user_message, bot_response, session_id))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"❌ Chat log error: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("🔒 MySQL connection closed")

    def test_connection(self):
        """Test database connection"""
        try:
            if self.ensure_connection():
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                if result:
                    print("✅ Database connection test: SUCCESS")
                    return True
            return False
        except Exception as e:
            print(f"❌ Database connection test failed: {e}")
            return False
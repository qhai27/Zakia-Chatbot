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
        self.password = password or ''       # Change this to your MySQL password
        self.database = database or 'lznk_chatbot'
        self.connection = None
        self.max_retries = 3
        self.retry_delay = 2

        # Create pool only once
        if DatabaseManager._pool is None:
            self._init_pool()

    # -----------------------------------------------------------
    # INITIALIZE POOL (FIXED)
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
    # CONNECT FUNCTION (FIXED & ENHANCED)
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
    # ENSURE CONNECTION (ENHANCED)
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
    # CREATE DATABASE (FIXED)
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

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS faqs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    category VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_category (category)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id VARCHAR(100) UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_last_activity (last_activity)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    user_message TEXT NOT NULL,
                    bot_response TEXT NOT NULL,
                    session_id VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_session (session_id),
                    INDEX idx_created (created_at),
                    INDEX idx_user_id (user_id),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
                    FOREIGN KEY (session_id) REFERENCES users(session_id) ON DELETE SET NULL ON UPDATE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

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
    # ADD FOREIGN KEYS (MIGRATION)
    # -----------------------------------------------------------
    def add_foreign_keys(self):
        """Add foreign key constraints to existing tables if they don't exist"""
        if not self.ensure_connection():
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # Check if foreign keys already exist and add them if not
            # For chat_logs.user_id -> users.id
            try:
                cursor.execute("""
                    SELECT CONSTRAINT_NAME 
                    FROM information_schema.KEY_COLUMN_USAGE 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'chat_logs' 
                    AND COLUMN_NAME = 'user_id' 
                    AND REFERENCED_TABLE_NAME = 'users'
                """)
                if not cursor.fetchone():
                    # Add user_id column if it doesn't exist
                    try:
                        cursor.execute("ALTER TABLE chat_logs ADD COLUMN user_id INT NULL AFTER id")
                        cursor.execute("ALTER TABLE chat_logs ADD INDEX idx_user_id (user_id)")
                    except Error as e:
                        if "Duplicate column name" not in str(e):
                            print(f"⚠️ Could not add user_id column: {e}")
                    
                    # Add foreign key
                    try:
                        cursor.execute("""
                            ALTER TABLE chat_logs 
                            ADD CONSTRAINT fk_chat_logs_user_id 
                            FOREIGN KEY (user_id) REFERENCES users(id) 
                            ON DELETE SET NULL ON UPDATE CASCADE
                        """)
                        print("✅ Added foreign key: chat_logs.user_id -> users.id")
                    except Error as e:
                        if "Duplicate foreign key" not in str(e) and "already exists" not in str(e):
                            print(f"⚠️ Could not add foreign key for user_id: {e}")
            except Error as e:
                print(f"⚠️ Error checking/adding user_id foreign key: {e}")
            
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
            
            # For reminders.user_id -> users.id
            try:
                cursor.execute("SHOW TABLES LIKE 'reminders'")
                if cursor.fetchone():
                    cursor.execute("""
                        SELECT CONSTRAINT_NAME 
                        FROM information_schema.KEY_COLUMN_USAGE 
                        WHERE TABLE_SCHEMA = DATABASE() 
                        AND TABLE_NAME = 'reminders' 
                        AND COLUMN_NAME = 'user_id' 
                        AND REFERENCED_TABLE_NAME = 'users'
                    """)
                    if not cursor.fetchone():
                        # Add user_id column if it doesn't exist
                        try:
                            cursor.execute("ALTER TABLE reminders ADD COLUMN user_id INT NULL AFTER id")
                            cursor.execute("ALTER TABLE reminders ADD INDEX idx_user_id (user_id)")
                        except Error as e:
                            if "Duplicate column name" not in str(e):
                                print(f"⚠️ Could not add user_id column to reminders: {e}")
                        
                        # Add foreign key
                        try:
                            cursor.execute("""
                                ALTER TABLE reminders 
                                ADD CONSTRAINT fk_reminders_user_id 
                                FOREIGN KEY (user_id) REFERENCES users(id) 
                                ON DELETE SET NULL ON UPDATE CASCADE
                            """)
                            print("✅ Added foreign key: reminders.user_id -> users.id")
                        except Error as e:
                            if "Duplicate foreign key" not in str(e) and "already exists" not in str(e):
                                print(f"⚠️ Could not add foreign key for reminders.user_id: {e}")
            except Error as e:
                print(f"⚠️ Error checking/adding reminders foreign key: {e}")
            
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

    # -----------------------------------------------------------
    # CRUD FAQ
    # -----------------------------------------------------------
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
            cursor.execute("SELECT * FROM faqs WHERE id = %s", (faq_id,))
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
                WHERE id=%s
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
            cursor.execute("DELETE FROM faqs WHERE id=%s", (faq_id,))
            self.connection.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0
        except Error as e:
            print(f"❌ FAQ delete error: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    # -----------------------------------------------------------
    # LOG CHAT (FIXED)
    # -----------------------------------------------------------
    def log_chat(self, user_message, bot_response, session_id=None):
        if not self.ensure_connection():
            print("⚠️ Cannot log chat - no database connection")
            return False
        try:
            cursor = self.connection.cursor()
            
            # Get user_id from session_id if provided
            user_id = None
            if session_id:
                try:
                    cursor.execute("SELECT id FROM users WHERE session_id = %s", (session_id,))
                    user_result = cursor.fetchone()
                    if user_result:
                        user_id = user_result[0]
                except Error:
                    pass  # Continue without user_id if lookup fails
            
            # Insert chat log with user_id if available
            cursor.execute("""
                INSERT INTO chat_logs (user_id, user_message, bot_response, session_id)
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

    # -----------------------------------------------------------
    # CLOSE
    # -----------------------------------------------------------
    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("🔒 MySQL connection closed")

    # -----------------------------------------------------------
    # TEST CONNECTION
    # -----------------------------------------------------------
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
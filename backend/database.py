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
                    id_faq INT AUTO_INCREMENT PRIMARY KEY,
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
                    id_user INT AUTO_INCREMENT PRIMARY KEY,
                    session_id VARCHAR(100) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_last_activity (last_activity),
                    INDEX idx_created_at (created_at),
                    INDEX idx_session_id (session_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

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
                    # First, create users for all existing session_ids in chat_logs that don't have a user
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
                    # If foreign key fails, at least we've migrated the data
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

    # -----------------------------------------------------------
    # USER MANAGEMENT
    # -----------------------------------------------------------
    def get_or_create_user(self, session_id):
        """
        Get or create a user by session_id.
        Returns user_id if successful, None otherwise.
        """
        if not session_id:
            return None
            
        if not self.ensure_connection():
            print("⚠️ Cannot get/create user - no database connection")
            return None
            
        try:
            cursor = self.connection.cursor()
            
            # Try to get existing user
            cursor.execute("SELECT id_user FROM users WHERE session_id = %s", (session_id,))
            user_result = cursor.fetchone()
            
            if user_result:
                # User exists, update last_activity and return id_user
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
                # User doesn't exist, create new one
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

    # -----------------------------------------------------------
    # LOG CHAT (FIXED - Now creates users automatically)
    # -----------------------------------------------------------
    def log_chat(self, user_message, bot_response, session_id=None):
        if not self.ensure_connection():
            print("⚠️ Cannot log chat - no database connection")
            return False
        try:
            cursor = self.connection.cursor()
            
            # Get or create user by session_id
            user_id = None
            if session_id:
                user_id = self.get_or_create_user(session_id)
            
            # Insert chat log with id_user if available
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

    # -----------------------------------------------------------
    # DATA MIGRATION METHODS
    # -----------------------------------------------------------
    def migrate_chat_logs_to_users(self):
        """
        Migrate existing chat_logs session_ids to users table.
        This fixes the foreign key constraint issue by creating users
        for all existing session_ids in chat_logs.
        """
        if not self.ensure_connection():
            return False
        
        try:
            cursor = self.connection.cursor()
            
            print("🔄 Starting migration: chat_logs session_ids -> users table...")
            
            # Step 1: Create users for all unique session_ids in chat_logs
            cursor.execute("""
                INSERT INTO users (session_id, created_at, last_activity)
                SELECT DISTINCT 
                    session_id,
                    MIN(created_at) as created_at,
                    MAX(created_at) as last_activity
                FROM chat_logs
                WHERE session_id IS NOT NULL
                AND session_id NOT IN (
                    SELECT session_id FROM users WHERE session_id IS NOT NULL
                )
                GROUP BY session_id
            """)
            created_users = cursor.rowcount
            print(f"✅ Created {created_users} users from existing chat_logs")
            
            # Step 2: Update id_user in chat_logs
            cursor.execute("""
                UPDATE chat_logs cl
                INNER JOIN users u ON cl.session_id = u.session_id
                SET cl.id_user = u.id_user
                WHERE cl.id_user IS NULL AND cl.session_id IS NOT NULL
            """)
            updated_logs = cursor.rowcount
            print(f"✅ Updated {updated_logs} chat_logs with user_id")
            
            # Step 3: Handle orphaned session_ids (set to NULL if they can't be migrated)
            cursor.execute("""
                SELECT COUNT(*) FROM chat_logs 
                WHERE session_id IS NOT NULL 
                AND session_id NOT IN (SELECT session_id FROM users WHERE session_id IS NOT NULL)
            """)
            orphaned_count = cursor.fetchone()[0]
            
            if orphaned_count > 0:
                print(f"⚠️ Found {orphaned_count} chat_logs with orphaned session_ids")
                print("   Setting orphaned session_ids to NULL...")
                cursor.execute("""
                    UPDATE chat_logs
                    SET session_id = NULL
                    WHERE session_id IS NOT NULL
                    AND session_id NOT IN (SELECT session_id FROM users WHERE session_id IS NOT NULL)
                """)
                print(f"✅ Set {cursor.rowcount} orphaned session_ids to NULL")
            
            self.connection.commit()
            cursor.close()
            
            print("✅ Migration completed successfully!")
            return True
            
        except Error as e:
            print(f"❌ Migration error: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    # -----------------------------------------------------------
    # USER MANAGEMENT METHODS
    # -----------------------------------------------------------
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        if not self.ensure_connection():
            return None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE id_user = %s", (user_id,))
            user = cursor.fetchone()
            cursor.close()
            return user
        except Error as e:
            print(f"❌ Error getting user by ID: {e}")
            return None

    def get_user_by_session_id(self, session_id):
        """Get user by session_id"""
        if not self.ensure_connection():
            return None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE session_id = %s", (session_id,))
            user = cursor.fetchone()
            cursor.close()
            return user
        except Error as e:
            print(f"❌ Error getting user by session_id: {e}")
            return None

    def list_users(self, limit=100, offset=0, order_by='last_activity', order_dir='DESC'):
        """List users with pagination"""
        if not self.ensure_connection():
            return []
        try:
            # Validate order_by to prevent SQL injection
            allowed_columns = ['id_user', 'session_id', 'created_at', 'last_activity']
            if order_by not in allowed_columns:
                order_by = 'last_activity'
            
            # Validate order direction
            order_dir = 'DESC' if order_dir.upper() == 'DESC' else 'ASC'
            
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(f"""
                SELECT * FROM users 
                ORDER BY {order_by} {order_dir}
                LIMIT %s OFFSET %s
            """, (limit, offset))
            users = cursor.fetchall()
            cursor.close()
            return users
        except Error as e:
            print(f"❌ Error listing users: {e}")
            return []

    def get_user_chat_history(self, user_id=None, session_id=None, limit=50):
        """Get chat history for a user"""
        if not self.ensure_connection():
            return []
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            if user_id:
                cursor.execute("""
                    SELECT * FROM chat_logs 
                    WHERE id_user = %s 
                    ORDER BY created_at DESC 
                    LIMIT %s
                """, (user_id, limit))
            elif session_id:
                cursor.execute("""
                    SELECT * FROM chat_logs 
                    WHERE session_id = %s 
                    ORDER BY created_at DESC 
                    LIMIT %s
                """, (session_id, limit))
            else:
                return []
            
            history = cursor.fetchall()
            cursor.close()
            return history
        except Error as e:
            print(f"❌ Error getting chat history: {e}")
            return []

    def get_user_stats(self, user_id):
        """Get statistics for a specific user"""
        if not self.ensure_connection():
            return None
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # Get user info
            cursor.execute("SELECT * FROM users WHERE id_user = %s", (user_id,))
            user = cursor.fetchone()
            
            if not user:
                cursor.close()
                return None
            
            # Get chat count
            cursor.execute("SELECT COUNT(*) as chat_count FROM chat_logs WHERE id_user = %s", (user_id,))
            chat_count = cursor.fetchone()['chat_count']
            
            # Reminder count is no longer available since reminders don't have user_id
            reminder_count = 0
            
            # Get first and last chat timestamps
            cursor.execute("""
                SELECT 
                    MIN(created_at) as first_chat,
                    MAX(created_at) as last_chat
                FROM chat_logs 
                WHERE id_user = %s
            """, (user_id,))
            chat_times = cursor.fetchone()
            
            cursor.close()
            
            return {
                'user': user,
                'chat_count': chat_count,
                'reminder_count': reminder_count,
                'first_chat': chat_times['first_chat'] if chat_times else None,
                'last_chat': chat_times['last_chat'] if chat_times else None
            }
        except Error as e:
            print(f"❌ Error getting user stats: {e}")
            return None

    def get_total_users_count(self):
        """Get total number of users"""
        if not self.ensure_connection():
            return 0
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            cursor.close()
            return count
        except Error as e:
            print(f"❌ Error getting users count: {e}")
            return 0

    def get_users_statistics(self):
        """Get overall users statistics"""
        if not self.ensure_connection():
            return None
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # Total users
            cursor.execute("SELECT COUNT(*) as total FROM users")
            total = cursor.fetchone()['total']
            
            # Active users (active in last 7 days)
            cursor.execute("""
                SELECT COUNT(*) as active 
                FROM users 
                WHERE last_activity >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            """)
            active = cursor.fetchone()['active']
            
            # New users today
            cursor.execute("""
                SELECT COUNT(*) as new_today 
                FROM users 
                WHERE DATE(created_at) = CURDATE()
            """)
            new_today = cursor.fetchone()['new_today']
            
            # Users with chats
            cursor.execute("""
                SELECT COUNT(DISTINCT id_user) as with_chats 
                FROM chat_logs 
                WHERE id_user IS NOT NULL
            """)
            with_chats = cursor.fetchone()['with_chats']
            
            cursor.close()
            
            return {
                'total_users': total,
                'active_users_7d': active,
                'new_users_today': new_today,
                'users_with_chats': with_chats
            }
        except Error as e:
            print(f"❌ Error getting users statistics: {e}")
            return None

    def delete_user(self, user_id):
        """Delete a user (cascades to chat_logs and reminders due to foreign keys)"""
        if not self.ensure_connection():
            return False
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM users WHERE id_user = %s", (user_id,))
            affected = cursor.rowcount
            self.connection.commit()
            cursor.close()
            return affected > 0
        except Error as e:
            print(f"❌ Error deleting user: {e}")
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
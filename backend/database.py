import mysql.connector
from mysql.connector import Error, pooling
import json
from datetime import datetime


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

        # Create pool only once
        if DatabaseManager._pool is None:
            self._init_pool()

    # -----------------------------------------------------------
    # INITIALIZE POOL
    # -----------------------------------------------------------
    def _init_pool(self):
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
                collation='utf8mb4_general_ci'
            )
            print("✅ Connection pool initialized")
        except Error as e:
            print(f"⚠️ Could not create connection pool: {e}")
            DatabaseManager._pool = None

    # -----------------------------------------------------------
    # CONNECT FUNCTION (FIXED & CLEAN)
    # -----------------------------------------------------------
    def connect(self):
        """Get connection from pool or fallback to direct connection."""
        # 1) Try pool first
        try:
            if DatabaseManager._pool is not None:
                self.connection = DatabaseManager._pool.get_connection()
                if self.connection.is_connected():
                    print("✅ Connection obtained from pool")
                    return True
        except Exception as e:
            print(f"⚠️ Pool connection failed: {e}. Fallback to direct...")

        # 2) Fallback direct connection
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
                use_pure=True
            )

            if self.connection.is_connected():
                print("✅ Direct MySQL connection established")
                return True

        except Error as e:
            print(f"❌ MySQL Connection Error: {e}")
            self.connection = None
            return False

    # -----------------------------------------------------------
    # ENSURE CONNECTION
    # -----------------------------------------------------------
    def ensure_connection(self):
        try:
            if self.connection is None or not self.connection.is_connected():
                print("⚠️ MySQL connection lost, reconnecting...")
                return self.connect()

            self.connection.ping(reconnect=True, attempts=3, delay=1)
            return True

        except Error:
            print("⚠️ Ping failed, reconnecting...")
            return self.connect()

    # -----------------------------------------------------------
    # CREATE DATABASE
    # -----------------------------------------------------------
    def create_database(self):
        try:
            conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                autocommit=True
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
            print(f"❌ Database creation error: {e}")
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
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_message TEXT NOT NULL,
                    bot_response TEXT NOT NULL,
                    session_id VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id VARCHAR(100) UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            self.connection.commit()
            cursor.close()
            print("✅ All tables are ready")
            return True

        except Error as e:
            print(f"❌ Table creation error: {e}")
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
                ("Apa itu zakat?", "Zakat ialah kewajipan agama...", "Umum"),
                ("Siapa yang wajib membayar zakat?", "Setiap Muslim...", "Umum"),
                ("Bagaimana cara membayar zakat?", "Melalui portal LZNK...", "Pembayaran"),
                ("Apakah waktu sesuai untuk bayar zakat?", "Akhir haul...", "Pembayaran"),
                ("Berapakah nisab zakat emas?", "85 gram...", "Nisab"),
                ("Berapakah kadar zakat emas?", "2.5%...", "Kadar"),
                ("Bagaimana mengira zakat perniagaan?", "2.5% modal kerja...", "Perniagaan"),
                ("Bilakah haul zakat bermula?", "12 bulan hijrah...", "Haul"),
                ("Apa itu LZNK?", "LZNK ialah badan zakat...", "LZNK"),
                ("Di mana lokasi pejabat LZNK?", "Alor Setar...", "LZNK"),
            ]

            cursor.executemany("""
                INSERT INTO faqs (question, answer, category)
                VALUES (%s, %s, %s)
            """, faqs)

            self.connection.commit()
            cursor.close()
            print("✅ FAQ inserted")

        except Error as e:
            print(f"❌ FAQ insert error: {e}")
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
            return False

    # -----------------------------------------------------------
    # LOG CHAT
    # -----------------------------------------------------------
    def log_chat(self, user_message, bot_response, session_id=None):
        if not self.ensure_connection():
            return False
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO chat_logs (user_message, bot_response, session_id)
                VALUES (%s, %s, %s)
            """, (user_message, bot_response, session_id))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"❌ Chat log error: {e}")
            return False

    # -----------------------------------------------------------
    # CLOSE
    # -----------------------------------------------------------
    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("🔒 MySQL connection closed")

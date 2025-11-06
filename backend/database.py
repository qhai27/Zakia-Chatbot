import mysql.connector
from mysql.connector import Error
import json
from datetime import datetime
from config import Config

class DatabaseManager:
    def __init__(self, host=None, user=None, password=None, database=None):
        # Default MySQL connection settings
        self.host = host or 'localhost'
        self.user = user or 'root'
        self.password = password or ''  # Change this to your MySQL password
        self.database = database or 'lznk_chatbot'
        self.connection = None
        
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.connection.is_connected():
                print("Connected to MySQL database")
                return True
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return False
    
    def create_database(self):
        """Create database if it doesn't exist"""
        try:
            connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password
            )
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            print(f"Database '{self.database}' created or already exists")
            cursor.close()
            connection.close()
            return True
        except Error as e:
            print(f"Error creating database: {e}")
            return False
    
    def create_tables(self):
        """Create necessary tables"""
        if not self.connection:
            return False
            
        try:
            cursor = self.connection.cursor()
            
            # FAQ table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS faqs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    category VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            # Chat logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_message TEXT NOT NULL,
                    bot_response TEXT NOT NULL,
                    session_id VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Users table for session management
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id VARCHAR(100) UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            self.connection.commit()
            cursor.close()
            print("Tables created successfully")
            return True
            
        except Error as e:
            print(f"Error creating tables: {e}")
            return False
    
    def insert_faqs(self):
        """Insert initial FAQ data"""
        if not self.connection:
            return False
            
        try:
            cursor = self.connection.cursor()
            
            # Check if FAQs already exist
            cursor.execute("SELECT COUNT(*) FROM faqs")
            count = cursor.fetchone()[0]
            
            if count > 0:
                print("FAQs already exist, skipping insertion")
                cursor.close()
                return True
            
            # Insert FAQ data
            faqs = [
                ("Apa itu zakat?", "Zakat ialah kewajipan agama yang dikenakan ke atas umat Islam untuk menunaikan sebahagian harta kepada golongan yang layak menerimanya.", "Umum"),
                ("Siapa yang wajib membayar zakat?", "Setiap Muslim yang cukup syarat seperti cukup haul, nisab, dan memiliki harta yang mencukupi.", "Umum"),
                ("Bagaimana cara membayar zakat?", "Anda boleh membayar zakat melalui portal rasmi LZNK, kaunter zakat, atau wakil amil yang dilantik.", "Pembayaran"),
                ("Apakah waktu sesuai untuk bayar zakat?", "Zakat boleh dibayar bila-bila masa, namun paling digalakkan pada akhir tahun haul atau bulan Ramadan.", "Pembayaran"),
                ("Berapakah nisab zakat emas?", "Nisab zakat emas ialah 85 gram atau nilai setara dengan 85 gram emas semasa.", "Nisab"),
                ("Berapakah kadar zakat emas?", "Kadar zakat emas ialah 2.5% daripada nilai emas yang mencukupi nisab.", "Kadar"),
                ("Bagaimana mengira zakat perniagaan?", "Zakat perniagaan dikira 2.5% daripada modal kerja dan keuntungan bersih selepas tolak hutang dan perbelanjaan operasi.", "Perniagaan"),
                ("Bilakah haul zakat bermula?", "Haul zakat bermula dari tarikh harta mencapai nisab dan berterusan selama 12 bulan hijrah.", "Haul"),
                # LZNK Company FAQs
                ("Apa itu LZNK?", "LZNK (Lembaga Zakat Negeri Kedah) ialah badan berkanun yang bertanggungjawab menguruskan zakat di Negeri Kedah Darul Aman.", "LZNK"),
                ("Di mana lokasi pejabat LZNK?", "Pejabat utama LZNK terletak di Alor Setar, Kedah. LZNK juga mempunyai cawangan di seluruh negeri Kedah.", "LZNK"),
                ("Apakah perkhidmatan yang ditawarkan LZNK?", "LZNK menawarkan perkhidmatan pengutipan zakat, pengagihan zakat kepada asnaf, pendidikan zakat, dan khidmat nasihat zakat.", "LZNK"),
                ("Bagaimana cara menghubungi LZNK?", "Anda boleh menghubungi LZNK melalui telefon, email, atau melawat pejabat LZNK yang terdekat.", "LZNK"),
                ("Apakah program bantuan LZNK?", "LZNK menjalankan pelbagai program bantuan untuk asnaf termasuk bantuan pendidikan, perubatan, dan keperluan asas.", "LZNK"),
                ("Bilakah LZNK ditubuhkan?", "LZNK ditubuhkan sebagai badan berkanun untuk menguruskan zakat di Negeri Kedah secara sistematik dan profesional.", "LZNK"),
                ("Siapa yang layak menerima bantuan LZNK?", "Bantuan LZNK diberikan kepada 8 golongan asnaf yang layak menerima zakat mengikut syariat Islam.", "LZNK"),
                ("Bagaimana LZNK memastikan ketelusan?", "LZNK mengamalkan prinsip ketelusan dalam pengurusan zakat dengan laporan kewangan yang boleh diakses oleh orang ramai.", "LZNK")
            ]
            
            cursor.executemany("""
                INSERT INTO faqs (question, answer, category) 
                VALUES (%s, %s, %s)
            """, faqs)
            
            self.connection.commit()
            cursor.close()
            print("FAQ data inserted successfully")
            return True
            
        except Error as e:
            print(f"Error inserting FAQs: {e}")
            return False
    
    def get_faqs(self):
        """Get all FAQs from database"""
        if not self.connection:
            return []
            
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM faqs ORDER BY category, question")
            faqs = cursor.fetchall()
            cursor.close()
            return faqs
        except Error as e:
            print(f"Error fetching FAQs: {e}")
            return []

    def get_faq_by_id(self, faq_id):
        """Get a single FAQ by id"""
        if not self.connection:
            return None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM faqs WHERE id = %s", (faq_id,))
            faq = cursor.fetchone()
            cursor.close()
            return faq
        except Error as e:
            print(f"Error fetching FAQ by id: {e}")
            return None

    def create_faq(self, question, answer, category=None):
        """Create a new FAQ"""
        if not self.connection:
            return None
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT INTO faqs (question, answer, category)
                VALUES (%s, %s, %s)
                """,
                (question, answer, category)
            )
            self.connection.commit()
            new_id = cursor.lastrowid
            cursor.close()
            return new_id
        except Error as e:
            print(f"Error creating FAQ: {e}")
            return None

    def update_faq(self, faq_id, question, answer, category=None):
        """Update an existing FAQ"""
        if not self.connection:
            return False
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                UPDATE faqs
                SET question = %s, answer = %s, category = %s
                WHERE id = %s
                """,
                (question, answer, category, faq_id)
            )
            self.connection.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0
        except Error as e:
            print(f"Error updating FAQ: {e}")
            return False

    def delete_faq(self, faq_id):
        """Delete an FAQ by id"""
        if not self.connection:
            return False
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM faqs WHERE id = %s", (faq_id,))
            self.connection.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0
        except Error as e:
            print(f"Error deleting FAQ: {e}")
            return False
    
    def log_chat(self, user_message, bot_response, session_id=None):
        """Log chat interaction"""
        if not self.connection:
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
            print(f"Error logging chat: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("MySQL connection closed")
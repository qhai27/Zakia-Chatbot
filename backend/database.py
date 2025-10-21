import mysql.connector
from mysql.connector import Error
import json
from datetime import datetime

class DatabaseManager:
    def __init__(self, host='localhost', user='root', password='', database='lznk_chatbot'):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
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
                ("Bilakah haul zakat bermula?", "Haul zakat bermula dari tarikh harta mencapai nisab dan berterusan selama 12 bulan hijrah.", "Haul")
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

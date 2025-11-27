"""
SQL Server Database Manager for ZAKIA Chatbot
Handles all database operations using SQL Server instead of MySQL
"""

import pyodbc
from sqlalchemy import create_engine, text
import pandas as pd
from datetime import datetime

class SQLServerDatabaseManager:
    def __init__(self, server=None, database=None, username=None, password=None):
        # SQL Server connection settings
        self.server = server or 'localhost'
        self.database = database or 'lznk_chatbot'
        self.username = username or 'sa'
        self.password = password or ''  # Change this to your SQL Server password
        self.engine = None
        
    def connect(self):
        """Establish SQL Server connection using SQLAlchemy"""
        try:
            # SQL Server connection string
            connection_string = f"mssql+pyodbc://{self.username}:{self.password}@{self.server}/{self.database}?driver=ODBC+Driver+17+for+SQL+Server"
            self.engine = create_engine(connection_string)
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            print("Connected to SQL Server database")
            return True
        except Exception as e:
            print(f"Error connecting to SQL Server: {e}")
            return False
    
    def create_database(self):
        """Create database if it doesn't exist"""
        try:
            # Connect to master database first
            master_connection_string = f"mssql+pyodbc://{self.username}:{self.password}@{self.server}/master?driver=ODBC+Driver+17+for+SQL+Server"
            master_engine = create_engine(master_connection_string)
            
            with master_engine.connect() as conn:
                conn.execute(text(f"IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '{self.database}') CREATE DATABASE {self.database}"))
                conn.commit()
            
            print(f"Database '{self.database}' created or already exists")
            return True
        except Exception as e:
            print(f"Error creating database: {e}")
            return False
    
    def create_tables(self):
        """Create necessary tables"""
        if not self.engine:
            return False
            
        try:
            with self.engine.connect() as conn:
                # FAQ table
                conn.execute(text("""
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='faqs' AND xtype='U')
                    CREATE TABLE faqs (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        question NVARCHAR(MAX) NOT NULL,
                        answer NVARCHAR(MAX) NOT NULL,
                        category NVARCHAR(100),
                        created_at DATETIME2 DEFAULT GETDATE(),
                        updated_at DATETIME2 DEFAULT GETDATE()
                    )
                """))
                
                # Users table for session management (must be created first for foreign keys)
                conn.execute(text("""
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' AND xtype='U')
                    CREATE TABLE users (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        session_id NVARCHAR(100) UNIQUE,
                        created_at DATETIME2 DEFAULT GETDATE(),
                        last_activity DATETIME2 DEFAULT GETDATE()
                    )
                """))
                
                # Chat logs table
                conn.execute(text("""
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='chat_logs' AND xtype='U')
                    CREATE TABLE chat_logs (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        user_id INT NULL,
                        user_message NVARCHAR(MAX) NOT NULL,
                        bot_response NVARCHAR(MAX) NOT NULL,
                        session_id NVARCHAR(100),
                        created_at DATETIME2 DEFAULT GETDATE(),
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
                        FOREIGN KEY (session_id) REFERENCES users(session_id) ON DELETE SET NULL ON UPDATE CASCADE
                    )
                """))
                
                conn.commit()
                print("Tables created successfully")
                return True
        except Exception as e:
            print(f"Error creating tables: {e}")
            return False
    
    def insert_faqs(self):
        """Insert initial FAQ data"""
        if not self.engine:
            return False
            
        try:
            with self.engine.connect() as conn:
                # Check if FAQs already exist
                result = conn.execute(text("SELECT COUNT(*) FROM faqs"))
                count = result.fetchone()[0]
                
                if count > 0:
                    print("FAQs already exist, skipping insertion")
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
                
                for question, answer, category in faqs:
                    conn.execute(text("""
                        INSERT INTO faqs (question, answer, category) 
                        VALUES (?, ?, ?)
                    """), (question, answer, category))
                
                conn.commit()
                print("FAQ data inserted successfully")
                return True
        except Exception as e:
            print(f"Error inserting FAQs: {e}")
            return False
    
    def get_faqs(self):
        """Get all FAQs from database"""
        if not self.engine:
            return []
            
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT * FROM faqs ORDER BY category, question"))
                faqs = []
                for row in result:
                    faqs.append({
                        'id': row[0],
                        'question': row[1],
                        'answer': row[2],
                        'category': row[3],
                        'created_at': row[4],
                        'updated_at': row[5]
                    })
                return faqs
        except Exception as e:
            print(f"Error fetching FAQs: {e}")
            return []
    
    def get_faq_by_id(self, faq_id):
        """Get a single FAQ by id"""
        if not self.engine:
            return None
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT * FROM faqs WHERE id = ?"), (faq_id,))
                row = result.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'question': row[1],
                        'answer': row[2],
                        'category': row[3],
                        'created_at': row[4],
                        'updated_at': row[5]
                    }
                return None
        except Exception as e:
            print(f"Error fetching FAQ by id: {e}")
            return None
    
    def create_faq(self, question, answer, category=None):
        """Create a new FAQ"""
        if not self.engine:
            return None
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    INSERT INTO faqs (question, answer, category)
                    OUTPUT INSERTED.id
                    VALUES (?, ?, ?)
                """), (question, answer, category))
                new_id = result.fetchone()[0]
                conn.commit()
                return new_id
        except Exception as e:
            print(f"Error creating FAQ: {e}")
            return None
    
    def update_faq(self, faq_id, question, answer, category=None):
        """Update an existing FAQ"""
        if not self.engine:
            return False
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    UPDATE faqs
                    SET question = ?, answer = ?, category = ?, updated_at = GETDATE()
                    WHERE id = ?
                """), (question, answer, category, faq_id))
                conn.commit()
                return result.rowcount > 0
        except Exception as e:
            print(f"Error updating FAQ: {e}")
            return False
    
    def delete_faq(self, faq_id):
        """Delete an FAQ by id"""
        if not self.engine:
            return False
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("DELETE FROM faqs WHERE id = ?"), (faq_id,))
                conn.commit()
                return result.rowcount > 0
        except Exception as e:
            print(f"Error deleting FAQ: {e}")
            return False
    
    def log_chat(self, user_message, bot_response, session_id=None):
        """Log chat interaction"""
        if not self.engine:
            return False
            
        try:
            with self.engine.connect() as conn:
                # Get user_id from session_id if provided
                user_id = None
                if session_id:
                    try:
                        result = conn.execute(text("SELECT id FROM users WHERE session_id = ?"), (session_id,))
                        user_row = result.fetchone()
                        if user_row:
                            user_id = user_row[0]
                    except Exception:
                        pass  # Continue without user_id if lookup fails
                
                conn.execute(text("""
                    INSERT INTO chat_logs (user_id, user_message, bot_response, session_id) 
                    VALUES (?, ?, ?, ?)
                """), (user_id, user_message, bot_response, session_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error logging chat: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            print("SQL Server connection closed")


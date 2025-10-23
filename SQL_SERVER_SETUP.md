# SQL Server Setup Guide for ZAKIA Chatbot

## 🔧 **Step-by-Step SQL Server Connection Setup**

### **Step 1: Install SQL Server**

#### Windows:
1. Download SQL Server Express (free) from: https://www.microsoft.com/en-us/sql-server/sql-server-downloads
2. Install SQL Server Express
3. During installation, choose "Mixed Mode Authentication"
4. Set a password for the 'sa' account

#### Alternative: SQL Server Developer Edition (free)
- Download from: https://www.microsoft.com/en-us/sql-server/sql-server-downloads
- Choose "Developer" edition (free for development)

### **Step 2: Install SQL Server Management Studio (SSMS)**
1. Download SSMS from: https://docs.microsoft.com/en-us/sql/ssms/download-sql-server-management-studio-ssms
2. Install SSMS for database management

### **Step 3: Start SQL Server Service**
1. Open Services.msc
2. Find "SQL Server (MSSQLSERVER)" or "SQL Server (SQLEXPRESS)"
3. Make sure it's running (Status: Running)

### **Step 4: Create Database and User**

Open SSMS and connect to your SQL Server instance:

```sql
-- Create database
CREATE DATABASE lznk_chatbot;

-- Use the database
USE lznk_chatbot;

-- Create user (optional, you can use sa)
CREATE LOGIN lznk_user WITH PASSWORD = 'your_password';
CREATE USER lznk_user FOR LOGIN lznk_user;
ALTER ROLE db_owner ADD MEMBER lznk_user;
```

### **Step 5: Configure Python Connection**

Update `backend/database.py` to use SQL Server instead of MySQL:

```python
import pyodbc
from sqlalchemy import create_engine
import pandas as pd

class DatabaseManager:
    def __init__(self, server=None, database=None, username=None, password=None):
        # SQL Server connection settings
        self.server = server or 'localhost'
        self.database = database or 'lznk_chatbot'
        self.username = username or 'sa'  # or 'lznk_user'
        self.password = password or 'your_sql_server_password'
        self.connection = None
        
    def connect(self):
        """Establish SQL Server connection"""
        try:
            # Connection string for SQL Server
            connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.server};DATABASE={self.database};UID={self.username};PWD={self.password}"
            self.connection = pyodbc.connect(connection_string)
            print("Connected to SQL Server database")
            return True
        except Exception as e:
            print(f"Error connecting to SQL Server: {e}")
            return False
```

### **Step 6: Install Required Python Packages**

```bash
pip install pyodbc
pip install sqlalchemy
pip install pandas
```

### **Step 7: Install ODBC Driver**

#### Windows:
1. Download "Microsoft ODBC Driver 17 for SQL Server" from:
   https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
2. Install the driver

#### Alternative Connection String (if ODBC Driver 17 doesn't work):
```python
connection_string = f"DRIVER={{SQL Server}};SERVER={self.server};DATABASE={self.database};UID={self.username};PWD={self.password}"
```

## 🔧 **Alternative: Using SQLAlchemy (Recommended)**

Create a new file `backend/sqlserver_database.py`:

```python
import pyodbc
from sqlalchemy import create_engine, text
import pandas as pd

class SQLServerDatabaseManager:
    def __init__(self, server=None, database=None, username=None, password=None):
        self.server = server or 'localhost'
        self.database = database or 'lznk_chatbot'
        self.username = username or 'sa'
        self.password = password or 'your_password'
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
                
                # Chat logs table
                conn.execute(text("""
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='chat_logs' AND xtype='U')
                    CREATE TABLE chat_logs (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        user_message NVARCHAR(MAX) NOT NULL,
                        bot_response NVARCHAR(MAX) NOT NULL,
                        session_id NVARCHAR(100),
                        created_at DATETIME2 DEFAULT GETDATE()
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
                    # Add more FAQs as needed
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
    
    def log_chat(self, user_message, bot_response, session_id=None):
        """Log chat interaction"""
        if not self.engine:
            return False
            
        try:
            with self.engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO chat_logs (user_message, bot_response, session_id) 
                    VALUES (?, ?, ?)
                """), (user_message, bot_response, session_id))
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
```

## 🚀 **Quick Setup Commands**

### **1. Install Dependencies**
```bash
pip install pyodbc sqlalchemy pandas
```

### **2. Update Database Configuration**
Edit `backend/database.py` or create `backend/sqlserver_database.py` with SQL Server settings.

### **3. Test Connection**
```bash
python test_sqlserver_connection.py
```

### **4. Set Up Database**
```bash
python setup_sqlserver_database.py
```

### **5. Start Chatbot**
```bash
python start_chatbot.py
```

## 🔍 **Common SQL Server Issues**

### **Issue 1: "Login failed for user"**
- Check your SQL Server username and password
- Make sure SQL Server is configured for Mixed Mode Authentication

### **Issue 2: "Cannot connect to server"**
- Make sure SQL Server service is running
- Check if SQL Server is listening on the correct port (usually 1433)

### **Issue 3: "ODBC Driver not found"**
- Install Microsoft ODBC Driver 17 for SQL Server
- Or use the alternative connection string with "SQL Server" driver

### **Issue 4: "Database does not exist"**
- Create the database in SSMS: `CREATE DATABASE lznk_chatbot;`

## 💡 **Connection String Examples**

### **For SQL Server Express:**
```python
server = 'localhost\\SQLEXPRESS'
```

### **For SQL Server Developer/Standard:**
```python
server = 'localhost'
```

### **For Named Instance:**
```python
server = 'localhost\\INSTANCENAME'
```

### **For Remote Server:**
```python
server = '192.168.1.100'  # IP address
```

## 🔧 **Alternative: Using Windows Authentication**

If you want to use Windows Authentication instead of SQL Server authentication:

```python
connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.server};DATABASE={self.database};Trusted_Connection=yes"
```

This uses your Windows login credentials instead of SQL Server username/password.

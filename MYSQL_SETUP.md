# MySQL Setup Guide for ZAKIA Chatbot

## 🔧 **Step-by-Step MySQL Connection Setup**

### **Step 1: Install MySQL Server**

#### Windows:
1. Download MySQL from: https://dev.mysql.com/downloads/mysql/
2. Install MySQL Server
3. Set a root password during installation

#### macOS:
```bash
brew install mysql
brew services start mysql
```

#### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install mysql-server
sudo mysql_secure_installation
```

### **Step 2: Start MySQL Service**

#### Windows:
- MySQL should start automatically
- Or use Services.msc to start MySQL service

#### macOS:
```bash
brew services start mysql
```

#### Linux:
```bash
sudo systemctl start mysql
sudo systemctl enable mysql
```

### **Step 3: Create Database and User**

Open MySQL command line or MySQL Workbench:

```sql
-- Connect to MySQL as root
mysql -u root -p

-- Create database
CREATE DATABASE lznk_chatbot;

-- Create user (optional, you can use root)
CREATE USER 'lznk_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON lznk_chatbot.* TO 'lznk_user'@'localhost';
FLUSH PRIVILEGES;

-- Exit MySQL
EXIT;
```

### **Step 4: Configure Database Connection**

Edit `backend/database.py` and update these lines:

```python
def __init__(self, host=None, user=None, password=None, database=None):
    # Update these values with your MySQL settings
    self.host = host or 'localhost'
    self.user = user or 'root'  # or 'lznk_user' if you created a user
    self.password = password or 'your_mysql_password'  # Your MySQL password
    self.database = database or 'lznk_chatbot'
    self.connection = None
```

### **Step 5: Test Connection**

Run this test script:

```bash
python -c "
from backend.database import DatabaseManager
db = DatabaseManager()
if db.connect():
    print('✅ MySQL connection successful!')
    db.close()
else:
    print('❌ MySQL connection failed!')
"
```

## 🔍 **Troubleshooting Common Issues**

### **Issue 1: "Access denied for user"**
**Solution:**
1. Check your MySQL username and password
2. Make sure the user has privileges:
   ```sql
   GRANT ALL PRIVILEGES ON lznk_chatbot.* TO 'your_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

### **Issue 2: "Can't connect to MySQL server"**
**Solutions:**
1. Make sure MySQL is running:
   ```bash
   # Windows: Check Services.msc
   # macOS: brew services list | grep mysql
   # Linux: sudo systemctl status mysql
   ```

2. Check if MySQL is listening on the correct port:
   ```bash
   netstat -an | grep 3306
   ```

### **Issue 3: "Unknown database 'lznk_chatbot'"**
**Solution:**
```sql
CREATE DATABASE lznk_chatbot;
```

### **Issue 4: "ModuleNotFoundError: No module named 'mysql'"**
**Solution:**
```bash
pip install mysql-connector-python
```

## 🚀 **Quick Setup Commands**

### **For Root User (Simplest):**
1. Update `backend/database.py`:
   ```python
   self.user = 'root'
   self.password = 'your_root_password'
   ```

2. Create database:
   ```sql
   CREATE DATABASE lznk_chatbot;
   ```

3. Run setup:
   ```bash
   python setup_database.py
   ```

### **For Custom User:**
1. Create user and database:
   ```sql
   CREATE DATABASE lznk_chatbot;
   CREATE USER 'lznk_user'@'localhost' IDENTIFIED BY 'secure_password';
   GRANT ALL PRIVILEGES ON lznk_chatbot.* TO 'lznk_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

2. Update `backend/database.py`:
   ```python
   self.user = 'lznk_user'
   self.password = 'secure_password'
   ```

## 🔧 **Alternative: Using Environment Variables**

Create a `.env` file in the `backend` directory:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=lznk_chatbot
```

Then the config will automatically use these values.

## ✅ **Test Your Connection**

Run this command to test everything:

```bash
python test_chatbot.py
```

You should see:
```
✅ Backend health check passed
✅ FAQs available: X items
✅ Chat endpoint working
🎉 All tests passed!
```

## 🆘 **Still Having Issues?**

1. **Check MySQL status:**
   ```bash
   mysql -u root -p -e "SELECT 1;"
   ```

2. **Check if database exists:**
   ```sql
   SHOW DATABASES;
   ```

3. **Check user privileges:**
   ```sql
   SHOW GRANTS FOR 'your_user'@'localhost';
   ```

4. **Check firewall/port:**
   ```bash
   telnet localhost 3306
   ```

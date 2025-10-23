# ZAKIA Chatbot Troubleshooting Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install -r backend/requirement.txt
```

### 2. Set up MySQL Database
Make sure MySQL is running and create a database:
```sql
CREATE DATABASE lznk_chatbot;
```

### 3. Update Database Configuration
Edit `backend/database.py` and update the connection parameters:
```python
def __init__(self, host='localhost', user='your_username', password='your_password', database='lznk_chatbot'):
```

### 4. Start the Chatbot
```bash
python start_chatbot.py
```

## Common Issues and Solutions

### Issue 1: "Chat won't reply" / No response from chatbot

**Possible Causes:**
1. Backend server not running
2. Database connection issues
3. CORS issues
4. JavaScript errors

**Solutions:**

#### Check Backend Server
1. Make sure the Flask server is running:
   ```bash
   cd backend
   python app.py
   ```
2. You should see:
   ```
   🚀 Starting ZAKIA Chatbot...
   ✅ Database initialized successfully
   ✅ NLP model initialized successfully
   🌐 Starting Flask server on http://localhost:5000
   * Running on all addresses (0.0.0.0)
   * Running on http://127.0.0.1:5000
   * Running on http://[your-ip]:5000
   ```

#### Check Database Connection
1. Verify MySQL is running
2. Check database credentials in `backend/database.py`
3. Test connection:
   ```bash
   cd backend
   python init_db.py
   ```

#### Check Frontend
1. Open browser developer tools (F12)
2. Check Console tab for JavaScript errors
3. Check Network tab for failed requests
4. Make sure `frontend/index.html` is opened in browser

### Issue 2: "Module not found" errors

**Solution:**
```bash
pip install -r backend/requirement.txt
```

### Issue 3: Database connection errors

**Solutions:**
1. Check MySQL is running
2. Verify database exists:
   ```sql
   SHOW DATABASES;
   ```
3. Check user permissions
4. Update connection parameters in `backend/database.py`

### Issue 4: CORS errors

**Solution:**
Make sure Flask-CORS is installed:
```bash
pip install flask-cors
```

## Testing the Chatbot

### 1. Test Backend API
Open browser and go to:
- `http://localhost:5000/health` - Should show health status
- `http://localhost:5000/faqs` - Should show FAQ data

### 2. Test Frontend
1. Open `frontend/index.html` in browser
2. Try sending a message
3. Check browser console for errors

### 3. Test Database
```bash
cd backend
python -c "from database import DatabaseManager; db = DatabaseManager(); print('Connected!' if db.connect() else 'Failed!')"
```

## Debug Mode

### Enable Debug Logging
Add this to `backend/app.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Logs
Look for error messages in the console output when starting the server.

## Quick Fixes

### Reset Everything
1. Stop the server (Ctrl+C)
2. Restart MySQL
3. Recreate database:
   ```sql
   DROP DATABASE lznk_chatbot;
   CREATE DATABASE lznk_chatbot;
   ```
4. Start server again

### Check File Permissions
Make sure all files are readable:
```bash
chmod -R 755 .
```

## Still Having Issues?

1. Check the console output for specific error messages
2. Verify all dependencies are installed
3. Make sure MySQL is running and accessible
4. Check that ports 5000 and 3306 are not blocked
5. Try running the initialization script: `python backend/init_db.py`

## Contact Support

If you're still having issues, please provide:
1. Error messages from console
2. Your operating system
3. Python version (`python --version`)
4. MySQL version
5. Steps you've already tried

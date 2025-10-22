# LZNK Zakat Chatbot

A modern, responsive chatbot for LZNK (Lembaga Zakat Negeri Kedah) built with Python Flask, MySQL, HTML, and CSS.

## Features

- 🤖 **Smart FAQ System**: AI-powered question matching using fuzzy string matching
- 💬 **Real-time Chat**: Interactive chat interface with typing indicators
- 🗄️ **MySQL Database**: Persistent storage for FAQs and chat logs
- 📱 **Responsive Design**: Works on desktop and mobile devices
- 🎯 **Quick Replies**: Pre-defined question buttons for easy interaction
- 📊 **Session Management**: Track user conversations
- 🔍 **Health Monitoring**: API health check endpoints

## Tech Stack

- **Backend**: Python Flask
- **Database**: MySQL
- **Frontend**: HTML5, CSS3, JavaScript
- **Styling**: Modern CSS with gradients and animations

## Prerequisites

- Python 3.7+
- MySQL Server
- pip (Python package manager)

## Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd lznk-chatbot
```

### 2. Install Python dependencies
```bash
pip install -r backend/requirement.txt
```

### 3. Set up MySQL Database

#### Option A: Using MySQL Command Line
```sql
CREATE DATABASE lznk_chatbot;
CREATE USER 'lznk_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON lznk_chatbot.* TO 'lznk_user'@'localhost';
FLUSH PRIVILEGES;
```

#### Option B: Using MySQL Workbench
1. Open MySQL Workbench
2. Create a new database named `lznk_chatbot`
3. Note your MySQL credentials

### 4. Configure Database Connection

Edit `backend/database.py` and update the connection parameters:
```python
def __init__(self, host='localhost', user='your_username', password='your_password', database='lznk_chatbot'):
```

### 5. Initialize Database
```bash
cd backend
python init_db.py
```

## Running the Application

### 1. Start the Backend Server
```bash
cd backend
python app.py
```
The server will start on `http://localhost:5000`

### 2. Open the Frontend
Open `frontend/index.html` in your web browser or serve it using a local server:
```bash
# Using Python's built-in server
cd frontend
python -m http.server 8000
```
Then visit `http://localhost:8000`

## API Endpoints

- `POST /chat` - Send a message to the chatbot
- `GET /faqs` - Get all FAQ questions and answers
- `GET /health` - Health check endpoint

## Database Schema

### Tables Created:
- `faqs` - Stores FAQ questions and answers
- `chat_logs` - Logs all chat interactions
- `users` - User session management

## Configuration

### Environment Variables (Optional)
Create a `.env` file in the backend directory:
```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=lznk_chatbot
FLASK_DEBUG=True
```

## Features in Detail

### Smart FAQ Matching
- Uses fuzzy string matching to find the best answer
- Configurable similarity threshold (default: 40%)
- Fallback responses for unmatched questions

### Session Management
- Unique session IDs for each conversation
- Chat history logging
- User activity tracking

### Responsive Design
- Mobile-first approach
- Touch-friendly interface
- Modern gradient backgrounds
- Smooth animations

## Troubleshooting

### Common Issues:

1. **MySQL Connection Error**
   - Ensure MySQL server is running
   - Check database credentials in `database.py`
   - Verify database exists

2. **Import Errors**
   - Run `pip install -r backend/requirement.txt`
   - Check Python version compatibility

3. **CORS Issues**
   - Ensure Flask-CORS is installed
   - Check browser console for errors

### Database Reset
To reset the database:
```bash
cd backend
python init_db.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support or questions, please contact the LZNK development team.




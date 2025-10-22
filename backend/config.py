import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Database configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'lznk_chatbot')
    
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'lznk-chatbot-secret-key')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'




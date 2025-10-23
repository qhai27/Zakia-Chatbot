"""
NLP Service for ZAKIA Chatbot
Handles NLP initialization and training
"""

from nlp_processor import NLPProcessor
from database import DatabaseManager

class NLPService:
    def __init__(self):
        self.nlp = NLPProcessor()
        self.db = DatabaseManager()
    
    def initialize_nlp(self):
        """Initialize and train the NLP model"""
        print("🚀 Initializing NLP model...")
        
        # Try to load pre-trained data
        if self.nlp.load_training_data('training_data.json'):
            print("✅ Loaded pre-trained model")
        else:
            # Train from scratch
            print("📚 Training model from FAQ data...")
            faqs = self.db.get_faqs()
            if faqs:
                self.nlp.train_from_faqs(faqs)
                self.nlp.save_training_data('training_data.json')
                print("✅ Model trained and saved")
            else:
                print("⚠️ No FAQ data available for training")
    
    def get_nlp_processor(self):
        """Get the NLP processor instance"""
        return self.nlp

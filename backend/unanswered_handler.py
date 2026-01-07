"""
Unanswered Questions Handler
Captures low-confidence responses for admin review
"""

from database import DatabaseManager

class UnansweredQuestionsHandler:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.confidence_threshold = 0.45  
        self.setup_table()
    
    def setup_table(self):
        """Create unanswered_questions table if not exists"""
        try:
            if not self.db.connection or not self.db.connection.is_connected():
                self.db.connect()
            
            cursor = self.db.connection.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS unanswered_questions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id VARCHAR(100),
                    question TEXT NOT NULL,
                    detected_intent VARCHAR(100),
                    confidence_score FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status ENUM('new', 'reviewed', 'answered') DEFAULT 'new',
                    admin_notes TEXT,
                    INDEX idx_status (status),
                    INDEX idx_created (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            self.db.connection.commit()
            cursor.close()
            
            print("✅ Unanswered questions table ready")
            
        except Exception as e:
            print(f"❌ Error setting up unanswered_questions table: {e}")
    
    def log_unanswered(self, session_id: str, question: str, 
                       detected_intent: str = None, confidence: float = 0.0):
        """
        Log an unanswered or low-confidence question
        
        Args:
            session_id: User session ID
            question: The question text
            detected_intent: Intent detected by NLP (if any)
            confidence: Confidence score (0-1)
        """
        try:
            # Only log if below confidence threshold
            if confidence >= self.confidence_threshold:
                return False
            
            if not self.db.connection or not self.db.connection.is_connected():
                self.db.connect()
            
            cursor = self.db.connection.cursor()
            
            # Check if similar question already logged recently (prevent spam)
            cursor.execute("""
                SELECT id FROM unanswered_questions
                WHERE question = %s
                AND DATE(created_at) = CURDATE()
                LIMIT 1
            """, (question,))
            
            if cursor.fetchone():
                cursor.close()
                return False  # Already logged today
            
            # Insert new unanswered question
            cursor.execute("""
                INSERT INTO unanswered_questions 
                (session_id, question, detected_intent, confidence_score)
                VALUES (%s, %s, %s, %s)
            """, (session_id, question, detected_intent, confidence))
            
            self.db.connection.commit()
            cursor.close()
            
            print(f"📝 Logged unanswered question: {question[:50]}... (confidence: {confidence:.2f})")
            return True
            
        except Exception as e:
            print(f"❌ Error logging unanswered question: {e}")
            return False
    
    def get_unanswered_stats(self):
        """Get statistics about unanswered questions"""
        try:
            if not self.db.connection or not self.db.connection.is_connected():
                self.db.connect()
            
            cursor = self.db.connection.cursor(dictionary=True)
            
            # Count by status
            cursor.execute("""
                SELECT 
                    status,
                    COUNT(*) as count
                FROM unanswered_questions
                GROUP BY status
            """)
            status_counts = cursor.fetchall()
            
            # Recent questions (last 7 days)
            cursor.execute("""
                SELECT COUNT(*) as recent_count
                FROM unanswered_questions
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            """)
            recent = cursor.fetchone()['recent_count']
            
            # Most common intents
            cursor.execute("""
                SELECT 
                    detected_intent,
                    COUNT(*) as count
                FROM unanswered_questions
                WHERE detected_intent IS NOT NULL
                GROUP BY detected_intent
                ORDER BY count DESC
                LIMIT 5
            """)
            top_intents = cursor.fetchall()
            
            cursor.close()
            
            return {
                "status_breakdown": status_counts,
                "recent_week": recent,
                "top_intents": top_intents
            }
            
        except Exception as e:
            print(f"❌ Error getting unanswered stats: {e}")
            return None
    
    def mark_as_reviewed(self, question_id: int, notes: str = None):
        """Mark question as reviewed"""
        try:
            if not self.db.connection or not self.db.connection.is_connected():
                self.db.connect()
            
            cursor = self.db.connection.cursor()
            
            cursor.execute("""
                UPDATE unanswered_questions
                SET status = 'reviewed',
                    admin_notes = %s
                WHERE id = %s
            """, (notes, question_id))
            
            self.db.connection.commit()
            cursor.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Error marking question as reviewed: {e}")
            return False
    
    def convert_to_faq(self, question_id: int, answer: str, category: str = 'Umum'):
        """
        Convert unanswered question to FAQ
        
        Args:
            question_id: ID of unanswered question
            answer: Answer to add
            category: FAQ category
        
        Returns:
            FAQ ID if successful, None otherwise
        """
        try:
            if not self.db.connection or not self.db.connection.is_connected():
                self.db.connect()
            
            cursor = self.db.connection.cursor(dictionary=True)
            
            # Get question text
            cursor.execute("""
                SELECT question FROM unanswered_questions
                WHERE id = %s
            """, (question_id,))
            
            result = cursor.fetchone()
            if not result:
                cursor.close()
                return None
            
            question = result['question']
            
            # Create FAQ
            faq_id = self.db.create_faq(question, answer, category)
            
            if faq_id:
                # Mark as answered
                cursor.execute("""
                    UPDATE unanswered_questions
                    SET status = 'answered'
                    WHERE id = %s
                """, (question_id,))
                
                self.db.connection.commit()
                print(f"✅ Converted question to FAQ #{faq_id}")
            
            cursor.close()
            return faq_id
            
        except Exception as e:
            print(f"❌ Error converting to FAQ: {e}")
            return None


# Integration helper
def integrate_with_chat_handler():
    """
    Example integration with chat handler
    Add this to your chat_routes.py
    """
    code_example = """
# In chat_routes.py, after NLP matching:

from unanswered_handler import UnansweredQuestionsHandler

# Initialize handler
unanswered_handler = UnansweredQuestionsHandler(db)

# In your chat endpoint, after getting response:
if response_data.get('confidence', 0) < 0.45:
    # Log as unanswered
    unanswered_handler.log_unanswered(
        session_id=session_id,
        question=user_input,
        detected_intent=intent.get('detected_intent'),
        confidence=response_data['confidence']
    )
"""
    return code_example
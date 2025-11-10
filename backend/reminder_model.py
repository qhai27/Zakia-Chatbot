"""
User Reminder Model for Zakat Payment System
Handles database schema for zakat payment reminders
"""

from datetime import datetime
from database import DatabaseManager
import mysql.connector
from mysql.connector import Error

class ReminderManager:
    def __init__(self, db_manager=None):
        self.db = db_manager or DatabaseManager()
        
    def create_reminder_table(self):
        """Create user_reminder table if it doesn't exist"""
        if not self.db.connection or not self.db.connection.is_connected():
            if not self.db.connect():
                print("❌ Failed to connect to database")
                return False
        
        try:
            cursor = self.db.connection.cursor()
            
            # Create user_reminder table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_reminder (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    ic_number VARCHAR(20) NOT NULL,
                    phone VARCHAR(20) NOT NULL,
                    zakat_type VARCHAR(50) NOT NULL,
                    zakat_amount DECIMAL(10,2) NOT NULL,
                    date_created DATETIME DEFAULT CURRENT_TIMESTAMP,
                    reminder_sent BOOLEAN DEFAULT FALSE,
                    INDEX idx_ic_number (ic_number),
                    INDEX idx_date_created (date_created)
                )
            """)
            
            self.db.connection.commit()
            cursor.close()
            print("✅ user_reminder table created successfully")
            return True
            
        except Error as e:
            print(f"❌ Error creating user_reminder table: {e}")
            return False
    
    def save_reminder(self, name, ic_number, phone, zakat_type, zakat_amount):
        """
        Save user reminder to database
        
        Args:
            name (str): User's full name
            ic_number (str): IC number without dashes
            phone (str): Phone number
            zakat_type (str): Type of zakat (pendapatan, simpanan, etc.)
            zakat_amount (float): Calculated zakat amount
            
        Returns:
            dict: Success status and message
        """
        if not self.db.connection or not self.db.connection.is_connected():
            if not self.db.connect():
                return {
                    'success': False,
                    'error': 'Gagal menyambung ke pangkalan data'
                }
        
        # Validation
        validation_result = self._validate_input(name, ic_number, phone, zakat_amount)
        if not validation_result['valid']:
            return {
                'success': False,
                'error': validation_result['error']
            }
        
        try:
            cursor = self.db.connection.cursor()
            
            # Insert reminder data
            cursor.execute("""
                INSERT INTO user_reminder 
                (name, ic_number, phone, zakat_type, zakat_amount)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                name.strip(),
                ic_number.strip(),
                phone.strip(),
                zakat_type,
                float(zakat_amount)
            ))
            
            self.db.connection.commit()
            reminder_id = cursor.lastrowid
            cursor.close()
            
            # Get first name for personalized message
            first_name = name.strip().split()[0]
            
            return {
                'success': True,
                'reminder_id': reminder_id,
                'reply': f"Terima kasih {first_name}! ✅ Maklumat anda telah direkod dan LZNK akan menghantar peringatan zakat anda nanti. 🤲"
            }
            
        except Error as e:
            print(f"❌ Error saving reminder: {e}")
            return {
                'success': False,
                'error': 'Ralat menyimpan maklumat. Sila cuba lagi.'
            }
    
    def _validate_input(self, name, ic_number, phone, zakat_amount):
        """
        Validate user input
        
        Returns:
            dict: Validation result with valid flag and error message
        """
        # Validate name
        if not name or len(name.strip()) < 3:
            return {
                'valid': False,
                'error': 'Sila masukkan nama penuh yang sah (sekurang-kurangnya 3 huruf)'
            }
        
        # Validate IC number (12 digits, no dashes)
        ic_clean = ic_number.strip().replace('-', '').replace(' ', '')
        if not ic_clean.isdigit() or len(ic_clean) != 12:
            return {
                'valid': False,
                'error': 'Nombor IC tidak sah. Sila masukkan 12 digit tanpa tanda sempang (contoh: 950101015678)'
            }
        
        # Validate phone number (10-11 digits, can start with 0 or +60)
        phone_clean = phone.strip().replace('-', '').replace(' ', '').replace('+', '')
        if phone_clean.startswith('60'):
            phone_clean = '0' + phone_clean[2:]
        
        if not phone_clean.isdigit() or len(phone_clean) < 10 or len(phone_clean) > 11:
            return {
                'valid': False,
                'error': 'Nombor telefon tidak sah. Sila masukkan nombor telefon Malaysia yang betul (contoh: 0123456789)'
            }
        
        # Validate zakat amount
        try:
            amount = float(zakat_amount)
            if amount <= 0:
                return {
                    'valid': False,
                    'error': 'Jumlah zakat tidak sah'
                }
        except (ValueError, TypeError):
            return {
                'valid': False,
                'error': 'Jumlah zakat tidak sah'
            }
        
        return {'valid': True}
    
    def get_reminders(self, limit=100):
        """Get all reminders (for admin purposes)"""
        if not self.db.connection or not self.db.connection.is_connected():
            if not self.db.connect():
                return []
        
        try:
            cursor = self.db.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM user_reminder 
                ORDER BY date_created DESC 
                LIMIT %s
            """, (limit,))
            reminders = cursor.fetchall()
            cursor.close()
            return reminders
        except Error as e:
            print(f"Error fetching reminders: {e}")
            return []
    
    def get_pending_reminders(self):
        """Get reminders that haven't been sent yet"""
        if not self.db.connection or not self.db.connection.is_connected():
            if not self.db.connect():
                return []
        
        try:
            cursor = self.db.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM user_reminder 
                WHERE reminder_sent = FALSE
                ORDER BY date_created ASC
            """)
            reminders = cursor.fetchall()
            cursor.close()
            return reminders
        except Error as e:
            print(f"Error fetching pending reminders: {e}")
            return []
    
    def mark_reminder_sent(self, reminder_id):
        """Mark a reminder as sent"""
        if not self.db.connection or not self.db.connection.is_connected():
            if not self.db.connect():
                return False
        
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                UPDATE user_reminder 
                SET reminder_sent = TRUE 
                WHERE id = %s
            """, (reminder_id,))
            self.db.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error marking reminder as sent: {e}")
            return False


# Initialize reminder table on import
if __name__ == "__main__":
    from database import DatabaseManager
    
    db = DatabaseManager()
    if db.connect():
        reminder_mgr = ReminderManager(db)
        reminder_mgr.create_reminder_table()
        print("✅ Reminder system initialized")
        db.close()
"""
User Reminder Model for Zakat Payment System
Handles database schema for zakat payment reminders
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from database import DatabaseManager

class ReminderManager:
    # default table name (avoid user_reminder)
    TABLE_NAME = "reminders"

    TABLE_SQL = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        ic_number VARCHAR(32) NOT NULL,
        phone VARCHAR(32) NOT NULL,
        zakat_type VARCHAR(64),
        zakat_amount DECIMAL(12,2),
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """

    def __init__(self, db: Optional[DatabaseManager] = None, auto_create: bool = False):
        """
        By default do NOT auto-create the table (auto_create=False).
        Set auto_create=True if you explicitly want the table created on init.
        """
        self.db = db or DatabaseManager()
        # Do not auto-create table to avoid unexpected schema changes
        if auto_create:
            self._ensure_table()

    def _ensure_table(self):
        """Create the reminders table if it doesn't exist (call explicitly if needed)."""
        try:
            if not self.db.connection:
                self.db.connect()
            cur = self.db.connection.cursor()
            cur.execute(self.TABLE_SQL)
            self.db.connection.commit()
            cur.close()
        except Exception as e:
            print("ReminderManager._ensure_table error:", e)

    # Backwards-compatible alias (if some code calls create_reminder_table)
    def create_reminder_table(self):
        return self._ensure_table()

    def validate(self, payload: Dict[str, Any]) -> Optional[str]:
        name = (payload.get('name') or '').strip()
        ic = (payload.get('ic_number') or '').replace('-', '').replace(' ', '')
        phone = (payload.get('phone') or '').strip()
        if not name or len(name) < 3:
            return "Nama tidak sah."
        if not ic or not ic.isdigit() or len(ic) != 12:
            return "Nombor IC mesti 12 digit tanpa tanda sempang."
        if not phone or not any(ch.isdigit() for ch in phone):
            return "Nombor telefon tidak sah."
        return None

    def save(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        err = self.validate(payload)
        if err:
            return {'success': False, 'error': err}
        try:
            if not self.db.connection:
                self.db.connect()
            conn = self.db.connection
            cur = conn.cursor()
            now = datetime.utcnow().replace(microsecond=0)
            zakat_amount = None
            try:
                zakat_amount = float(payload.get('zakat_amount')) if payload.get('zakat_amount') not in (None, '') else None
            except Exception:
                zakat_amount = None

            # INSERT into reminders table (no auto-create here)
            cur.execute(f"""
                INSERT INTO {self.TABLE_NAME}
                (name, ic_number, phone, zakat_type, zakat_amount, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                payload.get('name').strip(),
                payload.get('ic_number').replace('-', '').replace(' ', ''),
                payload.get('phone').strip(),
                payload.get('zakat_type'),
                zakat_amount,
                now, now
            ))
            conn.commit()
            insert_id = cur.lastrowid
            cur.close()
            return {'success': True, 'id': insert_id}
        except Exception as e:
            print("ReminderManager.save error:", e)
            return {'success': False, 'error': 'Gagal menyimpan maklumat.'}

    def list(self, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            if not self.db.connection:
                self.db.connect()
            cur = self.db.connection.cursor(dictionary=True)
            cur.execute(f"SELECT * FROM {self.TABLE_NAME} ORDER BY created_at DESC LIMIT %s", (limit,))
            rows = cur.fetchall()
            cur.close()
            return rows or []
        except Exception as e:
            print("ReminderManager.list error:", e)
            return []

# Initialize reminder table on import
if __name__ == "__main__":
    from database import DatabaseManager
    
    db = DatabaseManager()
    if db.connect():
        reminder_mgr = ReminderManager(db)
        reminder_mgr.create_reminder_table()
        print("✅ Reminder system initialized")
        db.close()
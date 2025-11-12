"""
User Reminder Model for Zakat Payment System
Handles database schema for zakat payment reminders
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from database import DatabaseManager

class ReminderManager:
    # default table name
    TABLE_NAME = "reminders"

    TABLE_SQL = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        ic_number VARCHAR(32) NOT NULL,
        phone VARCHAR(32) NOT NULL,
        zakat_type VARCHAR(64),
        zakat_amount DECIMAL(12,2),
        year VARCHAR(32),
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

            # Get year information
            year = payload.get('year', '')

            # INSERT into reminders table
            cur.execute(f"""
                INSERT INTO {self.TABLE_NAME}
                (name, ic_number, phone, zakat_type, zakat_amount, year, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                payload.get('name').strip(),
                payload.get('ic_number').replace('-', '').replace(' ', ''),
                payload.get('phone').strip(),
                payload.get('zakat_type'),
                zakat_amount,
                year,
                now, now
            ))
            conn.commit()
            insert_id = cur.lastrowid
            cur.close()
            return {'success': True, 'id': insert_id}
        except Exception as e:
            print("ReminderManager.save error:", e)
            return {'success': False, 'error': 'Gagal menyimpan maklumat.'}

    def list(self, limit: int = 100, offset: int = 0, search: str = '', zakat_type: str = '') -> List[Dict[str, Any]]:
        try:
            if not self.db.connection:
                self.db.connect()
            cur = self.db.connection.cursor(dictionary=True)
            
            # Build query with filters
            query = f"SELECT * FROM {self.TABLE_NAME} WHERE 1=1"
            params = []
            
            if search:
                query += " AND (name LIKE %s OR ic_number LIKE %s OR phone LIKE %s)"
                search_param = f"%{search}%"
                params.extend([search_param, search_param, search_param])
            
            if zakat_type:
                query += " AND zakat_type = %s"
                params.append(zakat_type)
            
            query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            cur.close()
            return rows or []
        except Exception as e:
            print("ReminderManager.list error:", e)
            return []

    def get_by_id(self, reminder_id: int) -> Optional[Dict[str, Any]]:
        try:
            if not self.db.connection:
                self.db.connect()
            cur = self.db.connection.cursor(dictionary=True)
            cur.execute(f"SELECT * FROM {self.TABLE_NAME} WHERE id = %s", (reminder_id,))
            row = cur.fetchone()
            cur.close()
            return row
        except Exception as e:
            print("ReminderManager.get_by_id error:", e)
            return None

    def delete(self, reminder_id: int) -> bool:
        try:
            if not self.db.connection:
                self.db.connect()
            cur = self.db.connection.cursor()
            cur.execute(f"DELETE FROM {self.TABLE_NAME} WHERE id = %s", (reminder_id,))
            self.db.connection.commit()
            affected = cur.rowcount
            cur.close()
            return affected > 0
        except Exception as e:
            print("ReminderManager.delete error:", e)
            return False

    def get_stats(self) -> Dict[str, Any]:
        try:
            if not self.db.connection:
                self.db.connect()
            cur = self.db.connection.cursor(dictionary=True)
            
            # Total count
            cur.execute(f"SELECT COUNT(*) as total FROM {self.TABLE_NAME}")
            total = cur.fetchone()['total']
            
            # Total amount
            cur.execute(f"SELECT SUM(zakat_amount) as total_amount FROM {self.TABLE_NAME}")
            total_amount = cur.fetchone()['total_amount'] or 0
            
            # By type
            cur.execute(f"""
                SELECT zakat_type, COUNT(*) as count, SUM(zakat_amount) as amount 
                FROM {self.TABLE_NAME} 
                GROUP BY zakat_type
            """)
            by_type = cur.fetchall()
            
            cur.close()
            
            return {
                'total': total,
                'total_amount': float(total_amount),
                'by_type': by_type
            }
        except Exception as e:
            print("ReminderManager.get_stats error:", e)
            return {'total': 0, 'total_amount': 0, 'by_type': []}
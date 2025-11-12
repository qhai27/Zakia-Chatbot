"""
User Reminder Model for Zakat Payment System
Fixed version with proper year field handling
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from database import DatabaseManager

class ReminderManager:
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
        updated_at DATETIME NOT NULL,
        INDEX idx_ic (ic_number),
        INDEX idx_phone (phone),
        INDEX idx_created (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """

    def __init__(self, db: Optional[DatabaseManager] = None, auto_create: bool = False):
        """
        Initialize ReminderManager
        
        Args:
            db: DatabaseManager instance
            auto_create: If True, create table on init
        """
        self.db = db or DatabaseManager()
        if auto_create:
            self._ensure_table()

    def _ensure_table(self):
        """Create the reminders table if it doesn't exist"""
        cur = None
        try:
            # Ensure connection is alive
            if not self.db.ensure_connection():
                print(f"❌ Cannot connect to database to create table '{self.TABLE_NAME}'")
                return False
            
            cur = self.db.connection.cursor()
            cur.execute(self.TABLE_SQL)
            self.db.connection.commit()
            print(f"✅ Table '{self.TABLE_NAME}' ensured")
            return True
        except Exception as e:
            print(f"❌ ReminderManager._ensure_table error: {e}")
            import traceback
            traceback.print_exc()
            # Try to rollback if there was an error
            try:
                if self.db.connection:
                    self.db.connection.rollback()
            except:
                pass
            return False
        finally:
            # Always close cursor
            if cur is not None:
                try:
                    cur.close()
                except:
                    pass

    def create_reminder_table(self):
        """Public method to create table"""
        return self._ensure_table()

    def validate(self, payload: Dict[str, Any]) -> Optional[str]:
        """
        Validate reminder data
        
        Returns:
            None if valid, error message if invalid
        """
        name = (payload.get('name') or '').strip()
        ic = (payload.get('ic_number') or '').replace('-', '').replace(' ', '')
        phone = (payload.get('phone') or '').strip()
        zakat_type = (payload.get('zakat_type') or '').strip().lower()
        
        # Validate name
        if not name or len(name) < 3:
            return "Nama tidak sah atau terlalu pendek."
        
        # Validate IC
        if not ic or not ic.isdigit() or len(ic) != 12:
            return "Nombor IC mesti 12 digit tanpa tanda sempang."
        
        # Validate phone
        if not phone or not any(ch.isdigit() for ch in phone):
            return "Nombor telefon tidak sah."
        
        # Validate zakat_type - must be 'pendapatan' or 'simpanan'
        if zakat_type and zakat_type not in ['pendapatan', 'simpanan']:
            return f"Jenis zakat tidak sah. Mesti 'pendapatan' atau 'simpanan'. Diterima: '{zakat_type}'"
        
        return None

    def save(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save reminder to database
        
        Args:
            payload: Dictionary containing reminder data
            
        Returns:
            Dictionary with success status and ID or error message
        """
        # Validate input
        err = self.validate(payload)
        if err:
            print(f"⚠️ Validation error: {err}")
            return {'success': False, 'error': err}
        
        try:
            # Ensure connection
            if not self.db.connection or not self.db.connection.is_connected():
                print("🔄 Reconnecting to database...")
                self.db.connect()
            
            conn = self.db.connection
            cur = conn.cursor()
            now = datetime.utcnow().replace(microsecond=0)
            
            # Parse zakat amount
            zakat_amount = None
            try:
                if payload.get('zakat_amount') not in (None, ''):
                    zakat_amount = float(payload.get('zakat_amount'))
            except (ValueError, TypeError):
                zakat_amount = None
            
            # Get year (with default empty string if not provided)
            year = payload.get('year', '').strip()
            
            # Clean data
            name = payload.get('name', '').strip()
            ic_number = payload.get('ic_number', '').replace('-', '').replace(' ', '')
            phone = payload.get('phone', '').strip()
            zakat_type = payload.get('zakat_type', '').strip().lower()
            
            # Validate zakat_type one more time before insert
            if zakat_type and zakat_type not in ['pendapatan', 'simpanan']:
                print(f"❌ Invalid zakat_type: {zakat_type}")
                return {'success': False, 'error': f'Jenis zakat tidak sah: {zakat_type}'}
            
            # Default to pendapatan if empty
            if not zakat_type:
                zakat_type = 'pendapatan'
            
            print(f"💾 Saving reminder - Name: {name}, IC: {ic_number}, Type: {zakat_type}, Year: {year}")
            
            # INSERT query
            sql = f"""
                INSERT INTO {self.TABLE_NAME}
                (name, ic_number, phone, zakat_type, zakat_amount, year, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                name,
                ic_number,
                phone,
                zakat_type,
                zakat_amount,
                year,
                now,
                now
            )
            
            cur.execute(sql, values)
            conn.commit()
            insert_id = cur.lastrowid
            cur.close()
            
            print(f"✅ Reminder saved with ID: {insert_id}")
            return {'success': True, 'id': insert_id}
            
        except Exception as e:
            print(f"❌ ReminderManager.save error: {e}")
            import traceback
            traceback.print_exc()
            
            # Try to rollback
            try:
                if self.db.connection:
                    self.db.connection.rollback()
            except:
                pass
            
            return {'success': False, 'error': 'Gagal menyimpan maklumat.'}

    def list(self, limit: int = 100, offset: int = 0, search: str = '', zakat_type: str = '') -> List[Dict[str, Any]]:
        """
        List reminders with optional filtering
        
        Args:
            limit: Maximum number of records
            offset: Starting position
            search: Search term for name, IC, or phone
            zakat_type: Filter by zakat type
            
        Returns:
            List of reminder dictionaries
        """
        cur = None
        try:
            # Ensure connection is alive
            if not self.db.ensure_connection():
                print("❌ Cannot establish database connection")
                return []
            
            # Ensure table exists
            if not self._ensure_table():
                print("⚠️ Could not ensure table exists, returning empty list")
                return []
            
            cur = self.db.connection.cursor(dictionary=True)
            
            # Build query
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
            
            return rows or []
            
        except Exception as e:
            print(f"❌ ReminderManager.list error: {e}")
            import traceback
            traceback.print_exc()
            
            # Try to reconnect and retry once
            retry_cur = None
            try:
                print("🔄 Retrying with fresh connection...")
                if self.db.ensure_connection() and self._ensure_table():
                    retry_cur = self.db.connection.cursor(dictionary=True)
                    # Rebuild query for retry
                    retry_query = f"SELECT * FROM {self.TABLE_NAME} WHERE 1=1"
                    retry_params = []
                    
                    if search:
                        retry_query += " AND (name LIKE %s OR ic_number LIKE %s OR phone LIKE %s)"
                        search_param = f"%{search}%"
                        retry_params.extend([search_param, search_param, search_param])
                    
                    if zakat_type:
                        retry_query += " AND zakat_type = %s"
                        retry_params.append(zakat_type)
                    
                    retry_query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                    retry_params.extend([limit, offset])
                    
                    retry_cur.execute(retry_query, tuple(retry_params))
                    rows = retry_cur.fetchall()
                    return rows or []
            except Exception as retry_error:
                print(f"❌ Retry also failed: {retry_error}")
                return []
            finally:
                # Always close retry cursor
                if retry_cur is not None:
                    try:
                        retry_cur.close()
                    except:
                        pass
            
            return []
        finally:
            # Always close cursor
            if cur is not None:
                try:
                    cur.close()
                except:
                    pass

    def get_by_id(self, reminder_id: int) -> Optional[Dict[str, Any]]:
        """Get single reminder by ID"""
        cur = None
        try:
            if not self.db.ensure_connection():
                print("❌ Cannot establish database connection for get_by_id")
                return None
            
            # Ensure table exists
            self._ensure_table()
            
            cur = self.db.connection.cursor(dictionary=True)
            cur.execute(f"SELECT * FROM {self.TABLE_NAME} WHERE id = %s", (reminder_id,))
            row = cur.fetchone()
            
            return row
            
        except Exception as e:
            print(f"❌ ReminderManager.get_by_id error: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            if cur is not None:
                try:
                    cur.close()
                except:
                    pass

    def delete(self, reminder_id: int) -> bool:
        """Delete reminder by ID"""
        cur = None
        try:
            if not self.db.ensure_connection():
                print("❌ Cannot establish database connection for delete")
                return False
            
            # Ensure table exists
            self._ensure_table()
            
            cur = self.db.connection.cursor()
            cur.execute(f"DELETE FROM {self.TABLE_NAME} WHERE id = %s", (reminder_id,))
            self.db.connection.commit()
            affected = cur.rowcount
            
            return affected > 0
            
        except Exception as e:
            print(f"❌ ReminderManager.delete error: {e}")
            import traceback
            traceback.print_exc()
            # Try to rollback on error
            try:
                if self.db.connection:
                    self.db.connection.rollback()
            except:
                pass
            return False
        finally:
            if cur is not None:
                try:
                    cur.close()
                except:
                    pass

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about reminders"""
        cur = None
        try:
            # Ensure connection and table exists
            if not self.db.ensure_connection():
                print("❌ Cannot establish database connection for stats")
                return {'total': 0, 'total_amount': 0, 'by_type': []}
            
            # Ensure table exists
            if not self._ensure_table():
                print("⚠️ Could not ensure table exists, returning empty stats")
                return {'total': 0, 'total_amount': 0, 'by_type': []}
            
            cur = self.db.connection.cursor(dictionary=True)
            
            # Total count
            cur.execute(f"SELECT COUNT(*) as total FROM {self.TABLE_NAME}")
            count_result = cur.fetchone()
            total = count_result['total'] if count_result else 0
            
            # Total amount
            cur.execute(f"SELECT COALESCE(SUM(zakat_amount), 0) as total_amount FROM {self.TABLE_NAME}")
            amount_result = cur.fetchone()
            total_amount = amount_result['total_amount'] if amount_result else 0
            
            # Convert Decimal to float if needed
            if hasattr(total_amount, '__float__'):
                total_amount = float(total_amount)
            elif total_amount is None:
                total_amount = 0.0
            
            # By type
            cur.execute(f"""
                SELECT 
                    zakat_type, 
                    COUNT(*) as count, 
                    COALESCE(SUM(zakat_amount), 0) as amount 
                FROM {self.TABLE_NAME} 
                GROUP BY zakat_type
            """)
            by_type = cur.fetchall() or []
            
            # Convert Decimal amounts to float in by_type results
            for item in by_type:
                if 'amount' in item and hasattr(item['amount'], '__float__'):
                    item['amount'] = float(item['amount'])
                elif 'amount' in item and item['amount'] is None:
                    item['amount'] = 0.0
            
            return {
                'total': int(total) if total else 0,
                'total_amount': float(total_amount),
                'by_type': by_type
            }
            
        except Exception as e:
            print(f"❌ ReminderManager.get_stats error: {e}")
            import traceback
            traceback.print_exc()
            return {'total': 0, 'total_amount': 0, 'by_type': []}
        finally:
            # Always close cursor
            if cur is not None:
                try:
                    cur.close()
                except:
                    pass
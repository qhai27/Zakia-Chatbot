"""
Clean up old undelivered live chat requests
These are responses that users will never see because they closed their session
"""

from database import DatabaseManager
from datetime import datetime, timedelta

def cleanup_old_requests():
    """Mark old undelivered requests as delivered so they don't clog the system"""
    db = DatabaseManager()
    
    if not db.connect():
        print("❌ Failed to connect to database")
        return
    
    cursor = db.connection.cursor(dictionary=True)
    
    # Find undelivered requests older than 1 hour
    one_hour_ago = datetime.now() - timedelta(hours=1)
    
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM live_chat_requests
        WHERE status = 'resolved'
        AND is_delivered = 0
        AND updated_at < %s
    """, (one_hour_ago,))
    
    old_count = cursor.fetchone()['count']
    
    if old_count == 0:
        print("✅ No old undelivered requests found")
        cursor.close()
        db.close()
        return
    
    print(f"\n⚠️  Found {old_count} old undelivered requests")
    print(f"   These are likely from closed sessions")
    print(f"   Marking them as delivered to clean up...\n")
    
    # Mark them as delivered
    cursor.execute("""
        UPDATE live_chat_requests
        SET is_delivered = 1,
            delivered_at = CURRENT_TIMESTAMP
        WHERE status = 'resolved'
        AND is_delivered = 0
        AND updated_at < %s
    """, (one_hour_ago,))
    
    db.connection.commit()
    affected = cursor.rowcount
    
    print(f"✅ Marked {affected} old requests as delivered")
    print(f"   They will no longer appear in pending list\n")
    
    cursor.close()
    db.close()

if __name__ == "__main__":
    cleanup_old_requests()
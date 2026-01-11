"""
Debug script to check live chat database state
Run this to see what's in the database
"""

from database import DatabaseManager

def debug_live_chat():
    db = DatabaseManager()
    
    if not db.connect():
        print("❌ Failed to connect to database")
        return
    
    cursor = db.connection.cursor(dictionary=True)
    
    print("\n" + "="*60)
    print("🔍 LIVE CHAT DEBUG")
    print("="*60 + "\n")
    
    # Check all live chat requests
    cursor.execute("""
        SELECT 
            id,
            session_id,
            user_message,
            bot_response,
            admin_response,
            admin_name,
            status,
            is_delivered,
            created_at,
            updated_at,
            delivered_at
        FROM live_chat_requests
        ORDER BY created_at DESC
        LIMIT 10
    """)
    
    requests = cursor.fetchall()
    
    if not requests:
        print("📭 No live chat requests found")
        cursor.close()
        db.close()
        return
    
    print(f"📊 Found {len(requests)} requests:\n")
    
    for req in requests:
        print(f"{'='*60}")
        print(f"🆔 Request ID: {req['id']}")
        print(f"🔑 Session ID: {req['session_id'][:16] if req['session_id'] else 'None'}...")
        print(f"📝 Status: {req['status']}")
        print(f"📬 Delivered: {'Yes' if req['is_delivered'] else 'No'}")
        print(f"\n👤 User Message:")
        print(f"   {req['user_message'][:80] if req['user_message'] else 'None'}...")
        print(f"\n🤖 Bot Response:")
        print(f"   {req['bot_response'][:80] if req['bot_response'] else 'None'}...")
        print(f"\n👨‍💼 Admin Response:")
        if req['admin_response']:
            print(f"   By: {req['admin_name'] or 'Unknown'}")
            print(f"   {req['admin_response'][:80]}...")
        else:
            print(f"   ⏳ No response yet")
        print(f"\n⏰ Timestamps:")
        print(f"   Created: {req['created_at']}")
        print(f"   Updated: {req['updated_at'] or 'N/A'}")
        print(f"   Delivered: {req['delivered_at'] or 'N/A'}")
        print()
    
    # Check for undelivered responses
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM live_chat_requests
        WHERE status = 'resolved'
        AND is_delivered = 0
        AND admin_response IS NOT NULL
    """)
    
    undelivered = cursor.fetchone()['count']
    
    if undelivered > 0:
        print(f"\n⚠️  WARNING: {undelivered} undelivered admin responses!")
        print("   These should be delivered to users.\n")
        
        cursor.execute("""
            SELECT id, session_id, admin_response, updated_at
            FROM live_chat_requests
            WHERE status = 'resolved'
            AND is_delivered = 0
            AND admin_response IS NOT NULL
        """)
        
        undelivered_list = cursor.fetchall()
        for item in undelivered_list:
            print(f"   • Request #{item['id']} | Session: {item['session_id'][:8]}...")
            print(f"     Response: {item['admin_response'][:50]}...")
            print(f"     Updated: {item['updated_at']}")
            print()
    
    # Check for open requests
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM live_chat_requests
        WHERE status = 'open'
    """)
    
    open_count = cursor.fetchone()['count']
    
    if open_count > 0:
        print(f"\n📢 {open_count} open requests waiting for admin response\n")
    
    cursor.close()
    db.close()
    
    print("="*60)
    print("✅ Debug complete")
    print("="*60 + "\n")

if __name__ == "__main__":
    debug_live_chat()
"""
Test the complete live chat flow
Creates a test request and verifies the polling works
"""

import requests
import time
import uuid

BASE_URL = "http://127.0.0.1:5000"

def test_live_chat_flow():
    print("\n" + "="*60)
    print("🧪 TESTING LIVE CHAT FLOW")
    print("="*60 + "\n")
    
    # Generate a fresh session ID
    session_id = str(uuid.uuid4())
    print(f"📝 Generated Session ID: {session_id[:16]}...\n")
    
    # Step 1: Create escalation request
    print("1️⃣  Creating escalation request...")
    
    request_data = {
        "session_id": session_id,
        "user_message": "Test question for live chat",
        "bot_response": "Test bot response"
    }
    
    response = requests.post(
        f"{BASE_URL}/live-chat/request",
        json=request_data
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to create request: {response.status_code}")
        print(response.text)
        return
    
    data = response.json()
    request_id = data.get('id')
    
    print(f"✅ Request created: ID = {request_id}")
    print(f"   Status: {data.get('status')}\n")
    
    # Step 2: Admin sends response (manual step)
    print("2️⃣  Now go to admin panel and send a response to request #{request_id}")
    print(f"   Session ID to verify: {session_id[:16]}...")
    print("\n   Waiting for admin to respond...")
    print("   Press Ctrl+C to cancel\n")
    
    # Step 3: Poll for admin response
    max_attempts = 60  # 3 minutes
    attempt = 0
    
    try:
        while attempt < max_attempts:
            attempt += 1
            time.sleep(3)
            
            print(f"⏱️  Attempt {attempt}: Polling for admin response...")
            
            poll_response = requests.get(
                f"{BASE_URL}/live-chat/pending",
                params={"session_id": session_id, "_t": str(int(time.time() * 1000))}
            )
            
            if poll_response.status_code != 200:
                print(f"   ❌ Poll failed: {poll_response.status_code}")
                continue
            
            poll_data = poll_response.json()
            
            if poll_data.get('pending') and poll_data.get('response'):
                print(f"\n✅ ADMIN RESPONSE RECEIVED!")
                print(f"\n{'='*60}")
                response_data = poll_data['response']
                print(f"🆔 Request ID: {response_data['id']}")
                print(f"👨‍💼 Admin: {response_data['admin_name']}")
                print(f"💬 Response: {response_data['admin_response']}")
                print(f"⏰ Updated: {response_data['updated_at']}")
                print(f"{'='*60}\n")
                
                print("✅ Live chat flow working correctly!")
                return True
            else:
                print(f"   ⏳ No response yet (pending: {poll_data.get('pending')})")
        
        print("\n⏰ Timeout: No admin response received after 3 minutes")
        return False
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user")
        return False

if __name__ == "__main__":
    test_live_chat_flow()
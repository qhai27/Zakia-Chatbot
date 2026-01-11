"""
Create a fresh test request for live chat testing
"""

import requests
import uuid

BASE_URL = "http://127.0.0.1:5000"

def create_test_request():
    print("\n" + "="*60)
    print("🧪 CREATING TEST LIVE CHAT REQUEST")
    print("="*60 + "\n")
    
    # Generate fresh session ID
    session_id = str(uuid.uuid4())
    
    print(f"📝 Session ID: {session_id}")
    print(f"   (First 16 chars: {session_id[:16]})\n")
    
    # Create request
    request_data = {
        "session_id": session_id,
        "user_message": "🧪 TEST: How do I calculate zakat?",
        "bot_response": "This is a test bot response for live chat testing."
    }
    
    print("📤 Sending request to server...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/live-chat/request",
            json=request_data
        )
        
        if response.status_code != 200:
            print(f"❌ Failed: {response.status_code}")
            print(response.text)
            return
        
        data = response.json()
        
        if not data.get('success'):
            print(f"❌ Request failed: {data.get('error')}")
            return
        
        request_id = data.get('id')
        
        print(f"\n✅ REQUEST CREATED SUCCESSFULLY!")
        print(f"\n{'='*60}")
        print(f"🆔 Request ID: {request_id}")
        print(f"🔑 Session ID: {session_id}")
        print(f"📝 Status: {data.get('status')}")
        print(f"{'='*60}\n")
        
        print("📋 NEXT STEPS:")
        print("1. Open admin panel: http://127.0.0.1:5000/admin.html")
        print("2. Click on 'Live Chat' section")
        print("3. Click 'Refresh' button")
        print("4. You should see the test request (ID: {})".format(request_id))
        print("5. Type a response and click 'Hantar'")
        print("\nThen run: python test_polling.py {}".format(session_id))
        
        # Save session ID to file for polling test
        with open('test_session_id.txt', 'w') as f:
            f.write(session_id)
        
        print("\n💾 Session ID saved to test_session_id.txt")
        print("\n" + "="*60 + "\n")
        
        return request_id, session_id
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, None

if __name__ == "__main__":
    create_test_request()
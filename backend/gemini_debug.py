"""
Enhanced Gemini Debugging Script
Run this to diagnose and fix Gemini integration issues
"""

import os
import sys
from dotenv import load_dotenv
import requests

print("="*70)
print("🔍 GEMINI API DIAGNOSTIC TOOL - ENHANCED")
print("="*70)

# Step 1: Check environment file
print("\n1️⃣ CHECKING .ENV FILE")
print("-"*70)

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    print(f"✅ GEMINI_API_KEY found")
    print(f"   Length: {len(api_key)} characters")
    print(f"   Starts with: {api_key[:10]}...")
    print(f"   Ends with: ...{api_key[-5:]}")
    
    # Validate format
    if len(api_key) < 30:
        print("   ⚠️ WARNING: API key seems too short (should be 39-40 chars)")
    if not api_key.startswith('AIza'):
        print("   ⚠️ WARNING: API key should start with 'AIza'")
else:
    print("❌ GEMINI_API_KEY not found in .env file!")
    print("\n💡 SOLUTION:")
    print("   1. Create/check backend/.env file")
    print("   2. Add this line:")
    print("      GEMINI_API_KEY=your_actual_api_key_here")
    print("   3. Get API key from: https://aistudio.google.com/app/apikey")
    sys.exit(1)

# Step 2: Check google-generativeai package
print("\n2️⃣ CHECKING GOOGLE-GENERATIVEAI PACKAGE")
print("-"*70)

try:
    import google.generativeai as genai
    print("✅ google-generativeai package installed")
    
    # Check version
    try:
        import pkg_resources
        version = pkg_resources.get_distribution("google-generativeai").version
        print(f"   Version: {version}")
    except:
        print("   Version: (unable to detect)")
        
except ImportError as e:
    print("❌ google-generativeai NOT installed!")
    print(f"   Error: {e}")
    print("\n💡 SOLUTION:")
    print("   pip install google-generativeai")
    sys.exit(1)

# Step 3: Test API key validity with REST API
print("\n3️⃣ TESTING API KEY WITH REST API")
print("-"*70)

try:
    print("   Testing API key validity...")
    
    # Use Gemini REST API to test key
    test_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    
    response = requests.get(test_url, timeout=10)
    
    print(f"   HTTP Status: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ API key is VALID!")
        data = response.json()
        
        if 'models' in data:
            print(f"   ✅ Found {len(data['models'])} available models")
            print("\n   Available models:")
            for model in data['models'][:5]:  # Show first 5
                model_name = model.get('name', '').replace('models/', '')
                print(f"      • {model_name}")
        
    elif response.status_code == 400:
        print("   ❌ API key format is INVALID")
        print(f"   Response: {response.text[:200]}")
        print("\n💡 SOLUTION:")
        print("   1. Check your API key is copied correctly")
        print("   2. No extra spaces or characters")
        print("   3. Get new key from: https://aistudio.google.com/app/apikey")
        sys.exit(1)
        
    elif response.status_code == 403:
        print("   ❌ API key DENIED (might be restricted)")
        print(f"   Response: {response.text[:200]}")
        print("\n💡 SOLUTION:")
        print("   1. Check API key restrictions in Google AI Studio")
        print("   2. Make sure Gemini API is enabled")
        print("   3. Try creating a new unrestricted key")
        sys.exit(1)
        
    elif response.status_code == 429:
        print("   ❌ QUOTA EXCEEDED!")
        print(f"   Response: {response.text[:200]}")
        print("\n💡 THIS IS YOUR PROBLEM!")
        print("\n   SOLUTIONS:")
        print("   1. WAIT: Quota resets after some time (usually 1 minute or 24 hours)")
        print("   2. NEW KEY: Create new API key in NEW PROJECT:")
        print("      → https://aistudio.google.com/app/apikey")
        print("      → Click 'Create API key in new project'")
        print("   3. NEW ACCOUNT: Use different Google account")
        print("   4. UPGRADE: Switch to paid plan for higher quota")
        print("\n   Free tier limits:")
        print("   • 15 requests per minute")
        print("   • 1 million tokens per day")
        print("   • 1,500 requests per day")
        sys.exit(1)
        
    else:
        print(f"   ⚠️ Unexpected status code: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        
except requests.exceptions.Timeout:
    print("   ❌ Request TIMEOUT - Network issue?")
    print("\n💡 SOLUTION:")
    print("   1. Check your internet connection")
    print("   2. Try again in a moment")
    sys.exit(1)
    
except requests.exceptions.ConnectionError:
    print("   ❌ CONNECTION ERROR - Cannot reach Google servers")
    print("\n💡 SOLUTION:")
    print("   1. Check your internet connection")
    print("   2. Check firewall settings")
    print("   3. Try using VPN if blocked")
    sys.exit(1)
    
except Exception as e:
    print(f"   ❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 4: Test with SDK
print("\n4️⃣ TESTING WITH GOOGLE GENAI SDK")
print("-"*70)

try:
    genai.configure(api_key=api_key)
    print("✅ SDK configured successfully")
    
    # Try different models
    models_to_test = [
        "gemini-2.0-flash-exp",
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-pro-latest",
        "gemini-pro"
    ]
    
    working_model = None
    
    print("\n   Testing models...")
    for model_name in models_to_test:
        try:
            print(f"\n   Trying: {model_name}")
            test_model = genai.GenerativeModel(model_name)
            
            response = test_model.generate_content(
                "Say 'OK'",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=50,
                )
            )
            
            if response.text:
                print(f"      ✅ SUCCESS! Response: {response.text.strip()}")
                working_model = model_name
                break
                
        except Exception as e:
            error_str = str(e)
            print(f"      ❌ Failed: {error_str[:100]}")
            
            if "429" in error_str or "quota" in error_str.lower():
                print(f"      💡 QUOTA ISSUE DETECTED!")
    
    if working_model:
        print(f"\n   ✅ Found working model: {working_model}")
    else:
        print("\n   ❌ No working models found!")
        print("\n   💡 LIKELY CAUSES:")
        print("   • Quota exceeded (429 error)")
        print("   • Invalid/expired API key")
        print("   • Network/firewall blocking")
        
except Exception as e:
    print(f"❌ SDK test failed: {e}")
    import traceback
    traceback.print_exc()

# Step 5: Check quota status
print("\n5️⃣ CHECKING QUOTA STATUS")
print("-"*70)

try:
    # Try to get quota info (this might not work for all keys)
    print("   Attempting to fetch quota information...")
    
    quota_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    test_payload = {
        "contents": [{
            "parts": [{"text": "test"}]
        }]
    }
    
    response = requests.post(quota_url, json=test_payload, timeout=10)
    
    if response.status_code == 429:
        print("   ❌ CONFIRMED: Quota exceeded")
        
        # Try to extract quota info from headers
        if 'retry-after' in response.headers:
            retry_after = response.headers['retry-after']
            print(f"   ⏰ Retry after: {retry_after} seconds")
        
        print("\n   📊 Your options:")
        print("   1. Wait for quota reset (check time above)")
        print("   2. Create new API key in new project")
        print("   3. Use different Google account")
        
    elif response.status_code == 200:
        print("   ✅ Quota appears OK - request succeeded")
        
except Exception as e:
    print(f"   ⚠️ Could not check quota: {e}")

# Step 6: Provide solutions
print("\n6️⃣ RECOMMENDED SOLUTIONS")
print("-"*70)

print("""
Based on the tests above, here are your options:

🎯 IMMEDIATE SOLUTIONS:

1. CREATE NEW API KEY IN NEW PROJECT (Recommended):
   → Go to: https://aistudio.google.com/app/apikey
   → Click "Create API Key"
   → Select "Create API key in new project" (IMPORTANT!)
   → Copy the new key
   → Update your .env file
   → Restart your app

2. USE DIFFERENT GOOGLE ACCOUNT:
   → Sign out from Google AI Studio
   → Sign in with different account
   → Create new API key
   → Each account gets separate quota

3. WAIT FOR QUOTA RESET:
   → Minute quota: Resets every 60 seconds
   → Daily quota: Resets at midnight PT (Pacific Time)
   → Check: https://aistudio.google.com/app/apikey

4. TEMPORARY: DISABLE GEMINI:
   → Edit backend/routes/chat_routes.py
   → Change: gemini = GeminiService()
   → To: gemini = None
   → Your chatbot will work with FAQ-only mode

5. UPGRADE TO PAID PLAN:
   → Enable billing in Google Cloud Console
   → Paid: 2,000 RPM (vs 15 RPM free)
   → Cost: ~$0.35 per 1M tokens
   → Much higher limits

📝 AFTER GETTING NEW KEY:

1. Update .env:
   GEMINI_API_KEY=your_new_key_here

2. Test again:
   python gemini_debug_script.py

3. Restart backend:
   python app.py

4. Verify in console:
   Should see: "✅ Connected to: gemini-xxx"
""")

print("\n" + "="*70)
print("✨ Diagnostic complete!")
print("="*70)

# Final status
print("\n📊 FINAL STATUS:")
if api_key:
    print("   • API Key: ✅ Present")
else:
    print("   • API Key: ❌ Missing")

try:
    import google.generativeai
    print("   • SDK Package: ✅ Installed")
except:
    print("   • SDK Package: ❌ Not installed")

print("\n💡 Next step: Follow solutions above based on your error")
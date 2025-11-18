"""
Gemini Debugging Script
Run this to diagnose Gemini integration issues
"""

import os
import sys
from dotenv import load_dotenv

print("="*70)
print("🔍 GEMINI API DIAGNOSTIC TOOL")
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
else:
    print("❌ GEMINI_API_KEY not found in .env file!")
    print("\n💡 SOLUTION:")
    print("   1. Create/check backend/.env file")
    print("   2. Add this line:")
    print("      GEMINI_API_KEY=your_actual_api_key_here")
    print("   3. Get API key from: https://makersuite.google.com/app/apikey")
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
    print("   pip install google-generativeai==0.3.1")
    sys.exit(1)

# Step 3: Test API connection
print("\n3️⃣ TESTING API CONNECTION")
print("-"*70)

try:
    genai.configure(api_key=api_key)
    print("✅ API configured successfully")
    
    # Test with simple prompt
    print("\n   Testing with simple prompt...")
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content("Say 'Hello from Gemini' if you can read this")
    
    response_text = response.text.strip()
    print(f"   ✅ Response received: {response_text[:80]}")
    
    if len(response_text) > 5:
        print("\n   ✅ Gemini is working correctly!")
    else:
        print("\n   ⚠️ Gemini responded but answer seems short")
        
except Exception as e:
    print(f"❌ API connection FAILED!")
    print(f"   Error: {e}")
    print("\n💡 POSSIBLE CAUSES:")
    print("   1. Invalid API key")
    print("   2. API key doesn't have access to Gemini 1.5 Flash")
    print("   3. Network/firewall issues")
    print("   4. API quota exceeded")
    print("\n💡 SOLUTIONS:")
    print("   1. Generate new API key at: https://makersuite.google.com/app/apikey")
    print("   2. Make sure API is enabled in Google Cloud Console")
    print("   3. Check your internet connection")
    sys.exit(1)

# Step 4: Test GeminiService class
print("\n4️⃣ TESTING GEMINI SERVICE CLASS")
print("-"*70)

try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from gemini_service import GeminiService
    
    print("✅ GeminiService imported successfully")
    
    gemini = GeminiService()
    print("✅ GeminiService initialized")
    
    # Test connection
    result = gemini.test_connection()
    if result.get('success'):
        print(f"✅ GeminiService test passed")
        print(f"   Response: {result.get('response', '')[:60]}...")
    else:
        print(f"❌ GeminiService test failed")
        print(f"   Error: {result.get('message')}")
        
except Exception as e:
    print(f"❌ GeminiService error: {e}")
    import traceback
    traceback.print_exc()
    print("\n💡 SOLUTION:")
    print("   Make sure gemini_service.py is in backend/ directory")
    sys.exit(1)

# Step 5: Test actual enhancement
print("\n5️⃣ TESTING ACTUAL ENHANCEMENT")
print("-"*70)

try:
    test_question = "Apa itu zakat?"
    test_faq_answer = "Zakat ialah kewajipan agama yang dikenakan ke atas umat Islam untuk menunaikan sebahagian harta kepada golongan yang layak menerimanya."
    
    print(f"   Question: {test_question}")
    print(f"   FAQ Answer: {test_faq_answer[:60]}...")
    
    enhanced = gemini.enhance_faq_response(test_question, test_faq_answer)
    
    print(f"\n   ✅ Enhancement successful!")
    print(f"   Enhanced answer:")
    print(f"   {enhanced[:200]}...")
    
    if len(enhanced) > len(test_faq_answer) * 0.5:
        print(f"\n   ✅ Enhancement looks good!")
    else:
        print(f"\n   ⚠️ Enhanced answer seems too short")
        
except Exception as e:
    print(f"❌ Enhancement test failed: {e}")
    import traceback
    traceback.print_exc()

# Step 6: Check Flask integration
print("\n6️⃣ CHECKING FLASK INTEGRATION")
print("-"*70)

try:
    # Check if chat_routes.py exists
    chat_routes_path = os.path.join(os.path.dirname(__file__), 'routes', 'chat_routes.py')
    if os.path.exists(chat_routes_path):
        print("✅ chat_routes.py found")
        
        with open(chat_routes_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        has_gemini_import = 'from gemini_service import GeminiService' in content
        has_gemini_init = 'gemini = GeminiService()' in content or 'gemini = None' in content
        
        print(f"   Gemini import: {'✅ YES' if has_gemini_import else '❌ NO'}")
        print(f"   Gemini initialization: {'✅ YES' if has_gemini_init else '❌ NO'}")
        
        if has_gemini_import and has_gemini_init:
            print("\n   ✅ Flask integration looks good!")
        else:
            print("\n   ⚠️ Flask integration incomplete")
            print("   Make sure you replaced chat_routes.py with the new version")
    else:
        print("❌ chat_routes.py not found")
        print(f"   Expected at: {chat_routes_path}")
        
except Exception as e:
    print(f"⚠️ Could not check Flask integration: {e}")

# Summary
print("\n" + "="*70)
print("📊 DIAGNOSTIC SUMMARY")
print("="*70)

print("""
✅ All checks passed!

🚀 NEXT STEPS:
1. Restart your Flask server: python app.py
2. Test the chat endpoint: curl -X POST http://localhost:5000/chat -H "Content-Type: application/json" -d '{"message": "Apa itu zakat?"}'
3. Check the debug endpoint: curl -X POST http://localhost:5000/debug-chat -H "Content-Type: application/json" -d '{"message": "test"}'
4. Monitor console logs for:
   💬 User messages
   🤖 Gemini enhancement logs
   ✅ Success messages

📝 TIPS:
- Look for "🤖 Enhancing FAQ answer with Gemini..." in console
- Check "enhanced_by_gemini": true in API response
- If Gemini not triggering, confidence might be too high (try lowering threshold)
- Use /debug-chat endpoint to see detailed diagnostics

❓ STILL NOT WORKING?
1. Check console logs when chatting
2. Use /test-gemini endpoint: curl http://localhost:5000/test-gemini
3. Try debug endpoint: curl -X POST http://localhost:5000/debug-chat -d '{"message":"test"}'
4. Share console output for more help
""")

print("="*70)
print("✨ Diagnostic complete!")
print("="*70)

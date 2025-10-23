#!/usr/bin/env python3
"""
Test Script for ZAKIA Chatbot
This script tests if the chatbot is working properly
"""

import sys
import os
import requests
import json

def test_backend():
    """Test if the backend is running"""
    try:
        # Test health endpoint
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend health check passed")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Make sure the server is running.")
        return False
    except Exception as e:
        print(f"❌ Backend test failed: {e}")
        return False

def test_faqs():
    """Test if FAQs are available"""
    try:
        response = requests.get("http://localhost:5000/faqs", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if 'faqs' in data and data['faqs']:
                print(f"✅ FAQs available: {len(data['faqs'])} items")
                return True
            else:
                print("❌ No FAQs found in response")
                return False
        else:
            print(f"❌ FAQ endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FAQ test failed: {e}")
        return False

def test_chat():
    """Test if chat endpoint works"""
    try:
        test_message = {
            "message": "Hello"
        }
        response = requests.post("http://localhost:5000/chat", 
                               json=test_message, 
                               headers={"Content-Type": "application/json"},
                               timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'reply' in data:
                print("✅ Chat endpoint working")
                print(f"   Test response: {data['reply'][:50]}...")
                return True
            else:
                print("❌ No reply in chat response")
                return False
        else:
            print(f"❌ Chat endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Chat test failed: {e}")
        return False

def main():
    print("🧪 ZAKIA Chatbot Test Suite")
    print("=" * 50)
    
    # Test backend
    if not test_backend():
        print("\n💡 Make sure to start the backend first:")
        print("   python start_chatbot.py")
        return False
    
    # Test FAQs
    if not test_faqs():
        print("\n💡 Run the database setup:")
        print("   python setup_database.py")
        return False
    
    # Test chat
    if not test_chat():
        print("\n💡 Check the backend logs for errors")
        return False
    
    print("\n🎉 All tests passed! Your chatbot is working correctly.")
    print("📱 Open frontend/index.html in your browser to use the chatbot.")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n🔧 Troubleshooting:")
        print("1. Make sure MySQL is running")
        print("2. Run: python setup_database.py")
        print("3. Run: python start_chatbot.py")
        print("4. Check backend/database.py for correct credentials")
        sys.exit(1)

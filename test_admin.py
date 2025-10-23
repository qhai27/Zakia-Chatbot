#!/usr/bin/env python3
"""
Admin Interface Test for ZAKIA Chatbot
This script tests the admin FAQ management functionality
"""

import sys
import os
import requests
import json

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_admin_endpoints():
    """Test all admin endpoints"""
    base_url = "http://localhost:5000/admin/faqs"
    
    print("Testing Admin FAQ Management")
    print("=" * 50)
    
    # Test 1: List FAQs
    print("1. Testing GET /admin/faqs...")
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            faqs = data.get('faqs', [])
            print(f"SUCCESS: Found {len(faqs)} FAQs")
        else:
            print(f"FAILED: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False
    
    # Test 2: Create FAQ
    print("2. Testing POST /admin/faqs...")
    try:
        test_faq = {
            "question": "Test FAQ Question",
            "answer": "This is a test FAQ answer for testing purposes.",
            "category": "Test"
        }
        
        response = requests.post(base_url, json=test_faq, timeout=5)
        if response.status_code == 201:
            data = response.json()
            faq_id = data.get('faq', {}).get('id')
            print(f"SUCCESS: Created FAQ with ID: {faq_id}")
        else:
            print(f"FAILED: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False
    
    # Test 3: Get specific FAQ
    print("3. Testing GET /admin/faqs/{id}...")
    try:
        response = requests.get(f"{base_url}/{faq_id}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Retrieved FAQ: {data.get('faq', {}).get('question')}")
        else:
            print(f"FAILED: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False
    
    # Test 4: Update FAQ
    print("4. Testing PUT /admin/faqs/{id}...")
    try:
        updated_faq = {
            "question": "Updated Test FAQ Question",
            "answer": "This is an updated test FAQ answer.",
            "category": "Updated Test"
        }
        
        response = requests.put(f"{base_url}/{faq_id}", json=updated_faq, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Updated FAQ: {data.get('faq', {}).get('question')}")
        else:
            print(f"FAILED: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False
    
    # Test 5: Delete FAQ
    print("5. Testing DELETE /admin/faqs/{id}...")
    try:
        response = requests.delete(f"{base_url}/{faq_id}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('deleted'):
                print("SUCCESS: FAQ deleted successfully")
            else:
                print("FAILED: Delete operation failed")
                return False
        else:
            print(f"FAILED: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False
    
    print("\nAll admin tests passed!")
    return True

def test_validation():
    """Test input validation"""
    print("\nTesting Input Validation")
    print("=" * 30)
    
    base_url = "http://localhost:5000/admin/faqs"
    
    # Test empty question
    print("1. Testing empty question...")
    try:
        response = requests.post(base_url, json={"answer": "test"}, timeout=5)
        if response.status_code == 400:
            print("SUCCESS: Correctly rejected empty question")
        else:
            print(f"FAILED: Should have rejected: HTTP {response.status_code}")
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test empty answer
    print("2. Testing empty answer...")
    try:
        response = requests.post(base_url, json={"question": "test"}, timeout=5)
        if response.status_code == 400:
            print("SUCCESS: Correctly rejected empty answer")
        else:
            print(f"FAILED: Should have rejected: HTTP {response.status_code}")
    except Exception as e:
        print(f"ERROR: {e}")

def main():
    print("ZAKIA Chatbot Admin Test Suite")
    print("=" * 50)
    
    try:
        # Test basic connectivity
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code != 200:
            print("FAILED: Backend server not running")
            print("Please start the backend with: python start_chatbot.py")
            return False
        
        print("SUCCESS: Backend server is running")
        
        # Test admin endpoints
        if not test_admin_endpoints():
            print("\nFAILED: Admin tests failed")
            return False
        
        # Test validation
        test_validation()
        
        print("\nAll tests completed successfully!")
        print("You can now use the admin interface at: frontend/admin.html")
        return True
        
    except requests.exceptions.ConnectionError:
        print("FAILED: Cannot connect to backend server")
        print("Please make sure the backend is running:")
        print("  python start_chatbot.py")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)

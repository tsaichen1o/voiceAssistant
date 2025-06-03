#!/usr/bin/env python3
"""
Test script to verify unified error response format
"""

import requests
import json

def test_error_formats():
    print("🧪 Testing Unified Error Response Formats\n")
    
    # Test 404 Error
    print("1. Testing 404 Error:")
    try:
        response = requests.get('http://localhost:8000/api/sessions/nonexistent')
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Request failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test Validation Error
    print("2. Testing Validation Error:")
    try:
        response = requests.post('http://localhost:8000/api/chat', 
            headers={
                'Authorization': 'Bearer test', 
                'Content-Type': 'application/json'
            },
            json={
                'messages': [
                    {
                        'role': 'invalid',  # Invalid role
                        'content': 'test'
                    }
                ]
            }
        )
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_error_formats() 
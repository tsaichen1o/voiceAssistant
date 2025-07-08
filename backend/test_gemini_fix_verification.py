#!/usr/bin/env python3
"""
🧪 Test Script: Gemini API Fix Verification

Quick test to verify that the Gemini API integration is working properly
after fixing the model compatibility issues.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.opensource_voice_service import opensource_voice_service

async def test_simple_gemini_call():
    """Test a simple Gemini API call to verify it's working."""
    print("🧪 Testing Simple Gemini API Call...")
    
    # Create test session
    user_id = f"fix_test_{int(datetime.now().timestamp())}"
    session_data = await opensource_voice_service.create_session(user_id, is_audio=False)
    session_id = session_data["session_id"]
    print(f"✅ Created test session: {session_id}")
    
    # Send simple test message
    test_message = "Say 'Hello, I am working correctly!'"
    print(f"📤 Sending test message: '{test_message}'")
    
    # Collect responses and check for actual success
    success = False
    error_messages = []
    complete_responses = []
    
    async for response in opensource_voice_service.send_message(session_id, test_message, "text/plain"):
        event_type = response.get("type")
        event_data = response.get("data", "")
        
        if event_type == "error":
            error_messages.append(response.get("error", "Unknown error"))
            print(f"   ❌ Error: {response.get('error', 'Unknown error')}")
        elif event_type == "text":
            print(f"   📨 Text: {event_data[:80]}...")
            if "Complete response:" in event_data and not response.get("partial", False):
                complete_responses.append(event_data)
                if "Hello, I am working correctly!" in event_data:
                    success = True
    
    # Cleanup
    await opensource_voice_service.close_session(session_id)
    
    # Report results
    if success:
        print("✅ Gemini API is working correctly!")
        print(f"   Got {len(complete_responses)} complete responses")
        return True
    else:
        print("❌ Gemini API is not working properly")
        if error_messages:
            print("   Errors encountered:")
            for error in error_messages:
                print(f"     - {error}")
        if not complete_responses:
            print("   No complete responses received")
        return False

async def test_model_configuration():
    """Test that the correct model is being used."""
    print("\n🔧 Testing Model Configuration...")
    
    # Check service health to see which model is configured
    health_status = await opensource_voice_service.health_check()
    print(f"Service status: {health_status}")
    
    # Check configuration
    from app.config import settings
    print(f"Configured VOICE_MODEL: {settings.VOICE_MODEL}")
    print(f"Configured GEMINI_MODEL: {settings.GEMINI_MODEL}")
    
    # Verify no 'live' models are being used
    if "live" in settings.VOICE_MODEL.lower():
        print("⚠️ Warning: VOICE_MODEL contains 'live' which may not support generateContent")
        return False
    else:
        print("✅ VOICE_MODEL is compatible with generateContent")
        return True

async def main():
    """Run verification tests."""
    print("🎯 Gemini API Fix Verification")
    print("=" * 50)
    
    tests = [
        ("Model Configuration", test_model_configuration()),
        ("Simple Gemini Call", test_simple_gemini_call()),
    ]
    
    results = []
    for test_name, test_coro in tests:
        print(f"\n{'='*15} {test_name} {'='*15}")
        try:
            result = await test_coro
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("🧪 Verification Summary:")
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📊 Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All fixes verified successfully!")
        print("🚀 Gemini API integration is working properly")
    else:
        print(f"\n⚠️ {len(results) - passed} tests failed")
        print("💡 Please check the configuration and ensure:")
        print("   - GEMINI_API_KEY is valid")
        print("   - Using a compatible model (not Live API models)")
        print("   - Network connectivity is working")

if __name__ == "__main__":
    asyncio.run(main()) 
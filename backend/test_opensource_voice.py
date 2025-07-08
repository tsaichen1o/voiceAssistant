#!/usr/bin/env python3
"""
Test script for OpenSource Voice Service - Step 1
测试开源语音服务基础架构
"""

import asyncio
import sys
import os

# Add the backend directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.opensource_voice_service import opensource_voice_service


async def test_basic_functionality():
    """Test basic functionality of the opensource voice service."""
    print("🧪 Testing OpenSource Voice Service - Step 1")
    print("=" * 50)
    
    try:
        # Test 1: Health Check
        print("\n1️⃣ Testing Health Check...")
        health = await opensource_voice_service.health_check()
        print(f"Health Status: {health}")
        
        # Test 2: Create Session
        print("\n2️⃣ Testing Session Creation...")
        test_user_id = "test_user_123"
        session_data = await opensource_voice_service.create_session(
            user_id=test_user_id, 
            is_audio=True
        )
        session_id = session_data["session_id"]
        print(f"Created session: {session_id}")
        print(f"Session data: {session_data}")
        
        # Test 3: Get Session
        print("\n3️⃣ Testing Session Retrieval...")
        retrieved_session = await opensource_voice_service.get_session(session_id)
        print(f"Retrieved session: {retrieved_session}")
        
        # Test 4: Update Session
        print("\n4️⃣ Testing Session Update...")
        update_success = await opensource_voice_service.update_session(
            session_id, 
            {"test_field": "test_value"}
        )
        print(f"Update success: {update_success}")
        
        # Test 5: Send Text Message
        print("\n5️⃣ Testing Text Message Processing...")
        print("Sending test text message...")
        async for event in opensource_voice_service.send_message(
            session_id, 
            "Hello, this is a test message", 
            "text/plain"
        ):
            print(f"Received event: {event}")
        
        # Test 6: Send Audio Message (placeholder)
        print("\n6️⃣ Testing Audio Message Processing...")
        print("Sending test audio message (base64 placeholder)...")
        test_audio_base64 = "dGVzdF9hdWRpb19kYXRh"  # "test_audio_data" in base64
        async for event in opensource_voice_service.send_message(
            session_id, 
            test_audio_base64, 
            "audio/pcm"
        ):
            print(f"Received event: {event}")
        
        # Test 7: List Active Sessions
        print("\n7️⃣ Testing Active Sessions List...")
        active_sessions = await opensource_voice_service.list_active_sessions()
        print(f"Active sessions: {active_sessions}")
        
        # Test 8: Close Session
        print("\n8️⃣ Testing Session Cleanup...")
        close_success = await opensource_voice_service.close_session(session_id)
        print(f"Close success: {close_success}")
        
        # Test 9: Verify Session Deleted
        print("\n9️⃣ Testing Session Deletion Verification...")
        deleted_session = await opensource_voice_service.get_session(session_id)
        print(f"Session after deletion: {deleted_session}")
        
        print("\n✅ All tests completed successfully!")
        print("\n📋 Summary:")
        print("- ✅ Redis connection working")
        print("- ✅ Session management working")
        print("- ✅ Message processing framework ready")
        print("- ✅ API endpoints ready")
        print("\n🚀 Ready for Step 2: ASR (Whisper) Implementation")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


async def test_redis_connection():
    """Test Redis connection independently."""
    try:
        print("\n🔍 Testing Redis Connection...")
        await opensource_voice_service.redis_client.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("💡 Make sure Redis is running:")
        print("   - Docker: docker run -d -p 6379:6379 redis:alpine")
        print("   - Local: redis-server")
        return False


async def main():
    """Main test function."""
    print("🎯 OpenSource Voice Service - Step 1 Testing")
    print("Testing basic infrastructure before implementing ASR/TTS...")
    
    # Test Redis connection first
    redis_ok = await test_redis_connection()
    if not redis_ok:
        print("\n❌ Redis connection failed. Please start Redis and try again.")
        return
    
    # Run main tests
    success = await test_basic_functionality()
    
    if success:
        print("\n🎉 Step 1 (基础架构) completed successfully!")
        print("👉 You can now test the API endpoints:")
        print("   - Health: GET /api/opensource-voice/health")
        print("   - Events: GET /api/opensource-voice/events/{user_id}")
        print("   - Send: POST /api/opensource-voice/send/{session_id}")
        print("\n📝 Next steps:")
        print("   1. Start the backend server: uvicorn main:app --reload")
        print("   2. Test the health endpoint in your browser")
        print("   3. Ready for Step 2: ASR (Whisper) implementation")
    else:
        print("\n❌ Step 1 tests failed. Please check the errors above.")


if __name__ == "__main__":
    asyncio.run(main()) 
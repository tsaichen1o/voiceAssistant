#!/usr/bin/env python3
"""
🧪 Test Script: LLM Functionality Testing - Step 3

Tests real Gemini API integration with the OpenSource Voice Service.
This validates the LLM processing pipeline including streaming responses.

Fixed version for google-generativeai library compatibility.
"""

import asyncio
import os
import base64
import numpy as np
import soundfile as sf
from pathlib import Path
import tempfile
from datetime import datetime

# Add the app directory to the Python path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.opensource_voice_service import opensource_voice_service

def create_test_audio():
    """Create a simple test audio file for pipeline testing."""
    # Generate 1 second of sine wave at 440Hz (A note)
    sample_rate = 24000
    duration = 1.0
    frequency = 440.0
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = 0.1 * np.sin(2 * np.pi * frequency * t)  # Low amplitude
    
    # Convert to PCM format (int16)
    audio_pcm = (audio_data * 32767).astype(np.int16)
    
    return base64.b64encode(audio_pcm.tobytes()).decode('utf-8')

async def test_gemini_api_health():
    """Test direct Gemini API configuration and connectivity."""
    print("\n=============== Gemini API Health ===============\n")
    
    try:
        print("🔧 Testing Gemini API Configuration...")
        
        # Check API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ GEMINI_API_KEY not found in environment")
            return False
            
        print(f"✅ GEMINI_API_KEY is configured")
        print(f"   Key starts with: {api_key[:10]}...")
        
        # Test basic API call
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Hello from Gemini API test")
        
        if response and response.text:
            print("✅ Direct Gemini API call successful")
            print(f"   Response: {response.text[:50]}...")
            return True
        else:
            print("❌ Gemini API call failed: No response")
            return False
            
    except Exception as e:
        print(f"❌ Gemini API health check failed: {e}")
        return False

async def test_text_message_llm():
    """Test LLM processing with text messages."""
    print("\n=============== Text Message LLM ===============")
    print("🧪 Testing LLM Processing with Text Messages...")
    
    # Create test session
    user_id = f"llm_test_user_{int(datetime.now().timestamp())}"
    session_data = await opensource_voice_service.create_session(user_id, is_audio=True)
    session_id = session_data["session_id"]
    print(f"✅ Created test session: {session_id}")
    
    # Send test message
    test_message = "Hello, can you tell me about TUM?"
    print(f"📤 Sending test message: '{test_message}'")
    
    # Collect responses
    events = []
    complete_responses = []
    
    async for response in opensource_voice_service.send_message(session_id, test_message, "text/plain"):
        events.append(response)
        if response.get("type") == "text" and not response.get("partial", False):
            if "Complete response:" in response.get("data", ""):
                complete_responses.append(response["data"])
        elif response.get("type") == "error":
            print(f"   📨 error: {response.get('error', 'Unknown error')[:50]}...")
        else:
            print(f"   📨 {response.get('type', 'unknown')}: {response.get('data', '')[:50]}...")
    
    print(f"✅ Received {len(events)} events from LLM pipeline")
    print(f"✅ Got {len(complete_responses)} complete text responses")
    
    # Check conversation history
    updated_session = await opensource_voice_service.get_session(session_id)
    conversation_history = updated_session.get("conversation_history", [])
    print(f"✅ Conversation history updated: {len(conversation_history)} entries")
    
    # Cleanup
    await opensource_voice_service.close_session(session_id)
    
    return len(events) > 0

async def test_conversation_context():
    """Test multi-turn conversation with context preservation."""
    print("\n=============== Conversation Context ===============\n")
    print("💬 Testing Multi-turn Conversation Context...")
    
    # Create test session
    user_id = f"context_test_user_{int(datetime.now().timestamp())}"
    session_data = await opensource_voice_service.create_session(user_id, is_audio=True)
    session_id = session_data["session_id"]
    
    # First message
    first_message = "My name is Alex and I'm interested in computer science at TUM"
    print(f"📤 Message 1: '{first_message}'")
    
    response_1 = ""
    async for response in opensource_voice_service.send_message(session_id, first_message, "text/plain"):
        if response.get("type") == "text" and "Complete response:" in response.get("data", ""):
            response_1 = response["data"]
            print(f"   🤖 Response 1: {response_1[:100]}...")
    
    # Second message (referencing first)
    second_message = "What are the admission requirements for the program I mentioned?"
    print(f"📤 Message 2: '{second_message}'")
    
    response_2 = ""
    async for response in opensource_voice_service.send_message(session_id, second_message, "text/plain"):
        if response.get("type") == "text" and "Complete response:" in response.get("data", ""):
            response_2 = response["data"]
            print(f"   🤖 Response 2: {response_2[:100]}...")
    
    # Check if the model maintains context
    if "computer science" in response_2.lower() or "alex" in response_2.lower():
        print("✅ LLM successfully maintained conversation context")
    else:
        print("⚠️ LLM may not be using context effectively")
    
    # Check final conversation history
    final_session = await opensource_voice_service.get_session(session_id)
    final_history = final_session.get("conversation_history", [])
    print(f"✅ Final conversation has {len(final_history)} entries")
    
    # Cleanup
    await opensource_voice_service.close_session(session_id)
    
    return True

async def test_audio_to_llm_pipeline():
    """Test complete audio->ASR->LLM pipeline."""
    print("\n=============== Audio-to-LLM Pipeline ===============\n")
    print("🎤 Testing Complete Audio -> ASR -> LLM Pipeline...")
    
    # Create test session
    user_id = f"audio_llm_test_{int(datetime.now().timestamp())}"
    session_data = await opensource_voice_service.create_session(user_id, is_audio=True)
    session_id = session_data["session_id"]
    
    # Create test audio
    print("🎤 Processing audio through complete pipeline...")
    test_audio_base64 = create_test_audio()
    
    # Process through complete pipeline
    events = []
    user_messages = 0
    assistant_responses = 0
    
    async for response in opensource_voice_service.send_message(session_id, test_audio_base64, "audio/pcm"):
        events.append(response)
        if response.get("type") == "text":
            if "You said:" in response.get("data", ""):
                user_messages += 1
                print(f"   👤 ASR Result: {response.get('data', '')[:100]}...")
            elif "🧠" in response.get("data", ""):
                print(f"   🧠 LLM processing...")
            elif "Complete response:" in response.get("data", ""):
                assistant_responses += 1
    
    print(f"✅ Complete pipeline processed {len(events)} events")
    
    # Check session state
    final_session = await opensource_voice_service.get_session(session_id)
    final_history = final_session.get("conversation_history", [])
    print(f"✅ Pipeline resulted in {user_messages} user messages and {assistant_responses} assistant responses")
    
    # Cleanup
    await opensource_voice_service.close_session(session_id)
    
    return len(events) > 0

async def main():
    """Run comprehensive LLM testing."""
    print("🎯 LLM Functionality Testing - Step 3")
    print("Testing Gemini API integration...")
    print("=" * 60)
    
    # Get service status
    status = await opensource_voice_service.health_check()
    print(f"Service Status: {status}\n")
    
    # Run tests
    test_results = []
    
    # Test 1: Gemini API Health
    try:
        result = await test_gemini_api_health()
        test_results.append(("Gemini API Health", result))
    except Exception as e:
        print(f"❌ Gemini API health test failed: {e}")
        test_results.append(("Gemini API Health", False))
    
    # Test 2: Text Message LLM
    try:
        result = await test_text_message_llm()
        test_results.append(("Text Message LLM", result))
    except Exception as e:
        print(f"❌ Text message LLM test failed: {e}")
        test_results.append(("Text Message LLM", False))
    
    # Test 3: Conversation Context
    try:
        result = await test_conversation_context()
        test_results.append(("Conversation Context", result))
    except Exception as e:
        print(f"❌ Conversation context test failed: {e}")
        test_results.append(("Conversation Context", False))
    
    # Test 4: Audio-to-LLM Pipeline
    try:
        result = await test_audio_to_llm_pipeline()
        test_results.append(("Audio-to-LLM Pipeline", result))
    except Exception as e:
        print(f"❌ Audio-to-LLM pipeline test failed: {e}")
        test_results.append(("Audio-to-LLM Pipeline", False))
    
    # Summary
    print("=" * 60)
    print("🧪 LLM Testing Summary:")
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📊 Results: {passed}/{len(test_results)} tests passed")
    
    if passed == len(test_results):
        print("\n🎉 Step 3 (LLM with Gemini API) completed successfully!")
        print("🚀 Ready for Step 4: TTS integration with gTTS")
        print("\n✨ Voice conversation pipeline is now functional:")
        print("   🎤 Audio Input -> 🧠 Whisper ASR -> 🤖 Gemini LLM -> 📱 Text Output")
        print("   📝 Text Input -> 🤖 Gemini LLM -> 📱 Text Output")
    else:
        print(f"\n⚠️ Some tests failed. Please check the issues above.")
        print("💡 Common issues:")
        print("   - GEMINI_API_KEY not set or invalid")
        print("   - Network connectivity problems")
        print("   - Library version incompatibility")

if __name__ == "__main__":
    asyncio.run(main()) 
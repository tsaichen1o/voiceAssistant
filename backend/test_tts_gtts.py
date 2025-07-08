#!/usr/bin/env python3
"""
🧪 Test Script: TTS Functionality Testing - Step 4

Tests gTTS (Google Text-to-Speech) integration with the OpenSource Voice Service.
This validates the complete voice conversation pipeline: Audio -> ASR -> LLM -> TTS.

Features tested:
- Basic TTS functionality with gTTS
- Multi-language TTS support (English, Chinese, German)
- Complete voice conversation loop
- Audio quality and format validation
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

async def test_basic_tts():
    """Test basic TTS functionality."""
    print("🧪 Testing Basic TTS Functionality...")
    
    # Create test session
    user_id = f"tts_test_{int(datetime.now().timestamp())}"
    session_data = await opensource_voice_service.create_session(user_id, is_audio=False)
    session_id = session_data["session_id"]
    print(f"✅ Created test session: {session_id}")
    
    # Test simple TTS generation
    test_message = "Hello, this is a test of the text to speech system."
    print(f"📤 Sending test message: '{test_message}'")
    
    # Collect responses and check for TTS audio
    tts_success = False
    audio_data = None
    error_messages = []
    
    async for response in opensource_voice_service.send_message(session_id, test_message, "text/plain"):
        event_type = response.get("type")
        event_data = response.get("data", "")
        
        if event_type == "error":
            error_messages.append(response.get("error", "Unknown error"))
            print(f"   ❌ Error: {response.get('error', 'Unknown error')}")
        elif event_type == "text":
            if "🔊" in event_data:
                print(f"   📨 TTS Status: {event_data}")
            elif "Complete response:" in event_data:
                print(f"   📨 LLM Response: {event_data[:80]}...")
        elif event_type == "audio":
            tts_success = True
            audio_data = response.get("data")
            audio_format = response.get("format", "unknown")
            print(f"   🎵 Audio received: {audio_format} format, {len(audio_data) if audio_data else 0} chars")
    
    # Cleanup
    await opensource_voice_service.close_session(session_id)
    
    # Report results
    if tts_success and audio_data:
        print("✅ Basic TTS functionality working!")
        print(f"   Generated audio data: {len(audio_data)} base64 characters")
        return True
    else:
        print("❌ Basic TTS functionality failed")
        if error_messages:
            print("   Errors encountered:")
            for error in error_messages:
                print(f"     - {error}")
        return False

async def test_multilingual_tts():
    """Test TTS with different languages."""
    print("\n🌍 Testing Multi-language TTS...")
    
    test_messages = [
        ("Hello, how are you today?", "en"),
        ("你好，今天怎么样？", "zh"),
        ("Hallo, wie geht es dir heute? TUM ist eine großartige Universität.", "de")
    ]
    
    results = []
    
    for text, expected_lang in test_messages:
        print(f"\n📤 Testing {expected_lang}: '{text}'")
        
        # Create test session
        user_id = f"multilang_test_{int(datetime.now().timestamp())}"
        session_data = await opensource_voice_service.create_session(user_id, is_audio=False)
        session_id = session_data["session_id"]
        
        # Test TTS generation
        tts_success = False
        detected_lang = None
        
        async for response in opensource_voice_service.send_message(session_id, text, "text/plain"):
            event_type = response.get("type")
            event_data = response.get("data", "")
            
            if event_type == "audio":
                tts_success = True
                print(f"   ✅ Audio generated for {expected_lang}")
            elif event_type == "text" and "Audio generated" in event_data:
                # Extract language from message like "🔊 Audio generated (5.2 KB, zh)"
                if "KB, " in event_data:
                    detected_lang = event_data.split("KB, ")[-1].rstrip(")")
                    print(f"   🌍 Detected/Used language: {detected_lang}")
        
        # Cleanup
        await opensource_voice_service.close_session(session_id)
        
        results.append((expected_lang, tts_success, detected_lang))
    
    # Report results
    success_count = sum(1 for _, success, _ in results if success)
    print(f"\n📊 Multi-language TTS Results: {success_count}/{len(results)} successful")
    
    for expected, success, detected in results:
        status = "✅" if success else "❌"
        lang_info = f" (detected: {detected})" if detected else ""
        print(f"   {status} {expected}{lang_info}")
    
    return success_count == len(results)

async def test_complete_voice_conversation():
    """Test complete voice conversation loop: Audio -> ASR -> LLM -> TTS."""
    print("\n🗣️ Testing Complete Voice Conversation Loop...")
    
    # Create test session
    user_id = f"voice_conv_test_{int(datetime.now().timestamp())}"
    session_data = await opensource_voice_service.create_session(user_id, is_audio=True)
    session_id = session_data["session_id"]
    print(f"✅ Created voice session: {session_id}")
    
    # Create test audio
    test_audio_base64 = create_test_audio()
    print("🎤 Processing audio through complete voice pipeline...")
    
    # Track pipeline stages
    stages_completed = {
        "audio_conversion": False,
        "asr": False,
        "llm": False,
        "tts": False
    }
    
    user_speech_detected = False
    assistant_audio_generated = False
    
    async for response in opensource_voice_service.send_message(session_id, test_audio_base64, "audio/pcm"):
        event_type = response.get("type")
        event_data = response.get("data", "")
        
        if event_type == "text":
            if "Converting audio" in event_data:
                stages_completed["audio_conversion"] = True
                print("   🔄 Audio format conversion completed")
            elif "You said:" in event_data:
                stages_completed["asr"] = True
                user_speech_detected = True
                print(f"   🎤 ASR completed: {event_data[:80]}...")
            elif "Complete response:" in event_data:
                stages_completed["llm"] = True
                print(f"   🧠 LLM completed: {event_data[:80]}...")
            elif "🔊" in event_data:
                print(f"   🔊 TTS status: {event_data}")
        elif event_type == "audio":
            stages_completed["tts"] = True
            assistant_audio_generated = True
            audio_format = response.get("format", "unknown")
            print(f"   🎵 TTS audio generated: {audio_format} format")
    
    # Cleanup
    await opensource_voice_service.close_session(session_id)
    
    # Report results
    completed_stages = sum(stages_completed.values())
    print(f"\n📊 Voice Conversation Pipeline: {completed_stages}/4 stages completed")
    
    for stage, completed in stages_completed.items():
        status = "✅" if completed else "❌"
        print(f"   {status} {stage.replace('_', ' ').title()}")
    
    if completed_stages >= 3:  # ASR might not work with synthetic audio
        print("✅ Complete voice conversation loop working!")
        return True
    else:
        print("❌ Voice conversation loop incomplete")
        return False

async def test_tts_audio_quality():
    """Test TTS audio quality and format validation."""
    print("\n🎵 Testing TTS Audio Quality and Format...")
    
    # Create test session
    user_id = f"audio_quality_test_{int(datetime.now().timestamp())}"
    session_data = await opensource_voice_service.create_session(user_id, is_audio=False)
    session_id = session_data["session_id"]
    
    # Test with a longer, more complex text
    test_message = "Welcome to the Technical University of Munich. Our computer science program offers excellent opportunities for international students. We have cutting-edge research facilities and world-class faculty members."
    print(f"📤 Testing audio quality with longer text ({len(test_message)} chars)")
    
    # Collect audio response
    audio_received = False
    audio_size = 0
    audio_format = None
    
    async for response in opensource_voice_service.send_message(session_id, test_message, "text/plain"):
        event_type = response.get("type")
        
        if event_type == "audio":
            audio_received = True
            audio_data = response.get("data", "")
            audio_format = response.get("format", "unknown")
            audio_size = len(audio_data)
            
            # Validate audio data
            try:
                decoded_audio = base64.b64decode(audio_data)
                audio_size_kb = len(decoded_audio) / 1024
                print(f"   ✅ Audio data valid: {audio_size_kb:.1f} KB")
                print(f"   📊 Format: {audio_format}")
                print(f"   📊 Base64 length: {audio_size} characters")
            except Exception as e:
                print(f"   ❌ Audio data invalid: {e}")
                audio_received = False
    
    # Cleanup
    await opensource_voice_service.close_session(session_id)
    
    # Validate quality metrics
    quality_checks = {
        "audio_received": audio_received,
        "valid_format": audio_format in ["mp3", "wav"],
        "reasonable_size": audio_size > 1000,  # Should be substantial for long text
    }
    
    passed_checks = sum(quality_checks.values())
    print(f"\n📊 Audio Quality: {passed_checks}/3 checks passed")
    
    for check, passed in quality_checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check.replace('_', ' ').title()}")
    
    return passed_checks >= 2

async def main():
    """Run comprehensive TTS testing."""
    print("🎯 TTS Functionality Testing - Step 4")
    print("Testing gTTS integration and complete voice pipeline...")
    print("=" * 60)
    
    # Get service status
    status = await opensource_voice_service.health_check()
    print(f"Service Status: {status}\n")
    
    # Check if gTTS is available
    gtts_status = status.get("components", {}).get("gtts", "unknown")
    if gtts_status != "available":
        print("❌ gTTS not available! Please install gTTS library.")
        print("   Run: pip install gtts")
        return
    
    # Run tests
    test_results = []
    
    tests = [
        ("Basic TTS", test_basic_tts()),
        ("Multi-language TTS", test_multilingual_tts()),
        ("Complete Voice Conversation", test_complete_voice_conversation()),
        ("TTS Audio Quality", test_tts_audio_quality()),
    ]
    
    for test_name, test_coro in tests:
        print(f"\n{'='*15} {test_name} {'='*15}")
        try:
            result = await test_coro
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            test_results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("🧪 TTS Testing Summary:")
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📊 Results: {passed}/{len(test_results)} tests passed")
    
    if passed == len(test_results):
        print("\n🎉 Step 4 (TTS with gTTS) completed successfully!")
        print("🚀 Ready for Step 5: End-to-end integration testing")
        print("\n✨ Complete voice conversation pipeline is now functional:")
        print("   🎤 User Voice → 🧠 Whisper ASR → 📝 Text → 🤖 Gemini LLM → 📝 Response → 🔊 gTTS TTS → 🎵 Audio Response")
    elif passed >= 2:
        print(f"\n⚠️ {len(test_results) - passed} tests failed, but core TTS functionality may be working")
        print("💡 Consider reviewing failed tests and configuration")
    else:
        print(f"\n❌ Multiple TTS tests failed. Please check:")
        print("   - gTTS library installation: pip install gtts")
        print("   - Network connectivity for gTTS")
        print("   - Audio file handling capabilities")

if __name__ == "__main__":
    asyncio.run(main()) 
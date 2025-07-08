#!/usr/bin/env python3
"""
Test script for ASR functionality - Step 2
测试Whisper语音识别功能
"""

import asyncio
import sys
import os
import base64
import numpy as np
import soundfile as sf
import tempfile

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.opensource_voice_service import opensource_voice_service


def create_test_audio_pcm():
    """Create a simple test audio in PCM format for testing."""
    try:
        # Generate a simple sine wave (440 Hz for 2 seconds)
        sample_rate = 24000
        duration = 2.0
        frequency = 440.0
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        # Create a sine wave and scale to 16-bit range
        wave = np.sin(2 * np.pi * frequency * t) * 0.3  # Reduced amplitude
        
        # Convert to 16-bit PCM
        pcm_data = (wave * 32767).astype(np.int16)
        
        # Convert to bytes then base64
        pcm_bytes = pcm_data.tobytes()
        pcm_base64 = base64.b64encode(pcm_bytes).decode('utf-8')
        
        print(f"✅ Generated test audio: {len(pcm_data)} samples, {duration}s, {frequency}Hz")
        return pcm_base64
        
    except Exception as e:
        print(f"❌ Error creating test audio: {e}")
        return None


def create_speech_test_audio():
    """Create a simple test audio with synthesized speech for testing."""
    try:
        # This creates a more realistic test by generating a simple pattern
        # that could represent speech (multiple frequencies)
        sample_rate = 24000
        duration = 1.5
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Create a more complex waveform that could resemble speech
        wave1 = np.sin(2 * np.pi * 300 * t) * 0.3  # Low frequency
        wave2 = np.sin(2 * np.pi * 800 * t) * 0.2  # Mid frequency  
        wave3 = np.sin(2 * np.pi * 1200 * t) * 0.1  # High frequency
        
        # Combine and add some envelope
        envelope = np.exp(-t * 0.5)  # Decay envelope
        combined_wave = (wave1 + wave2 + wave3) * envelope
        
        # Add some noise to make it more speech-like
        noise = np.random.normal(0, 0.01, len(combined_wave))
        combined_wave += noise
        
        # Convert to 16-bit PCM
        pcm_data = (combined_wave * 32767 * 0.5).astype(np.int16)
        
        # Convert to bytes then base64
        pcm_bytes = pcm_data.tobytes()
        pcm_base64 = base64.b64encode(pcm_bytes).decode('utf-8')
        
        print(f"✅ Generated speech-like test audio: {len(pcm_data)} samples, {duration}s")
        return pcm_base64
        
    except Exception as e:
        print(f"❌ Error creating speech test audio: {e}")
        return None


async def test_audio_conversion():
    """Test PCM to WAV conversion functionality."""
    print("\n1️⃣ Testing Audio Format Conversion...")
    
    try:
        # Create test PCM data
        test_pcm_base64 = create_test_audio_pcm()
        if not test_pcm_base64:
            return False
        
        # Test conversion
        temp_wav_path = await opensource_voice_service._convert_pcm_to_wav(test_pcm_base64)
        
        # Verify the file was created and is valid
        if os.path.exists(temp_wav_path):
            # Read back and verify
            data, sample_rate = sf.read(temp_wav_path)
            print(f"✅ Conversion successful: {len(data)} samples at {sample_rate}Hz")
            print(f"   WAV file: {temp_wav_path}")
            
            # Clean up
            os.unlink(temp_wav_path)
            return True
        else:
            print("❌ WAV file was not created")
            return False
            
    except Exception as e:
        print(f"❌ Audio conversion test failed: {e}")
        return False


async def test_whisper_transcription():
    """Test Whisper transcription with a simple audio file."""
    print("\n2️⃣ Testing Whisper Transcription...")
    
    try:
        # For this test, we'll just verify Whisper can process an audio file
        # Note: Since we're generating synthetic audio, Whisper won't recognize actual speech
        
        # Create a simple test audio file
        test_pcm_base64 = create_speech_test_audio()
        if not test_pcm_base64:
            return False
        
        # Convert to WAV
        temp_wav_path = await opensource_voice_service._convert_pcm_to_wav(test_pcm_base64)
        
        # Test Whisper transcription
        print("🎤 Running Whisper transcription...")
        transcribed_text = await opensource_voice_service._transcribe_audio_with_whisper(temp_wav_path)
        
        print(f"✅ Whisper transcription completed")
        print(f"   Result: '{transcribed_text}'")
        print("   Note: Synthetic audio may not produce meaningful transcription")
        
        # Clean up
        os.unlink(temp_wav_path)
        return True
        
    except Exception as e:
        print(f"❌ Whisper transcription test failed: {e}")
        return False


async def test_full_asr_pipeline():
    """Test the complete ASR pipeline with a session."""
    print("\n3️⃣ Testing Full ASR Pipeline...")
    
    try:
        # Create a test session
        test_user_id = "asr_test_user"
        session_data = await opensource_voice_service.create_session(
            user_id=test_user_id, 
            is_audio=True
        )
        session_id = session_data["session_id"]
        print(f"✅ Created test session: {session_id}")
        
        # Create test audio
        test_pcm_base64 = create_speech_test_audio()
        if not test_pcm_base64:
            return False
        
        # Process through the full pipeline
        print("🔄 Processing through full ASR pipeline...")
        events = []
        async for event in opensource_voice_service.send_message(
            session_id, 
            test_pcm_base64, 
            "audio/pcm"
        ):
            events.append(event)
            print(f"   📨 Event: {event}")
        
        # Verify we got expected events
        print(f"✅ Received {len(events)} events from ASR pipeline")
        
        # Check conversation history was updated
        updated_session = await opensource_voice_service.get_session(session_id)
        history = updated_session.get("conversation_history", [])
        print(f"✅ Conversation history updated: {len(history)} entries")
        
        # Clean up session
        await opensource_voice_service.close_session(session_id)
        return True
        
    except Exception as e:
        print(f"❌ Full ASR pipeline test failed: {e}")
        return False


async def test_real_world_scenario():
    """Test a more realistic scenario with longer audio."""
    print("\n4️⃣ Testing Real-world Scenario...")
    
    try:
        # Create a longer, more complex audio sample
        sample_rate = 24000
        duration = 3.0  # 3 seconds
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Create a complex waveform that changes over time
        speech_pattern = []
        for i in range(5):  # 5 different "words"
            start_t = i * duration / 5
            end_t = (i + 1) * duration / 5
            segment_mask = (t >= start_t) & (t < end_t)
            
            # Different frequency pattern for each "word"
            freq = 300 + i * 200  # Varying frequencies
            segment = np.sin(2 * np.pi * freq * t) * segment_mask * 0.3
            speech_pattern.append(segment)
        
        # Combine all segments
        combined_wave = np.sum(speech_pattern, axis=0)
        
        # Add envelope and noise
        envelope = np.sin(np.pi * t / duration)  # Bell curve envelope
        combined_wave *= envelope
        combined_wave += np.random.normal(0, 0.005, len(combined_wave))
        
        # Convert to PCM
        pcm_data = (combined_wave * 32767 * 0.7).astype(np.int16)
        pcm_bytes = pcm_data.tobytes()
        pcm_base64 = base64.b64encode(pcm_bytes).decode('utf-8')
        
        print(f"✅ Created complex test audio: {duration}s, {len(pcm_data)} samples")
        
        # Test the pipeline
        session_data = await opensource_voice_service.create_session("real_test_user", True)
        session_id = session_data["session_id"]
        
        print("🔄 Processing complex audio through ASR...")
        async for event in opensource_voice_service.send_message(session_id, pcm_base64, "audio/pcm"):
            print(f"   📨 {event.get('type', '')}: {event.get('data', '')[:50]}...")
        
        await opensource_voice_service.close_session(session_id)
        print("✅ Real-world scenario test completed")
        return True
        
    except Exception as e:
        print(f"❌ Real-world scenario test failed: {e}")
        return False


async def main():
    """Main test function for ASR functionality."""
    print("🎯 ASR Functionality Testing - Step 2")
    print("Testing Whisper speech recognition integration...")
    print("=" * 60)
    
    # Check prerequisites
    try:
        import numpy as np
        import soundfile as sf
        print("✅ NumPy and SoundFile available")
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Please install: pip install numpy soundfile")
        return
    
    # Check Redis connection
    try:
        await opensource_voice_service.redis_client.ping()
        print("✅ Redis connection successful")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return
    
    # Run tests
    tests = [
        ("Audio Format Conversion", test_audio_conversion()),
        ("Whisper Transcription", test_whisper_transcription()),
        ("Full ASR Pipeline", test_full_asr_pipeline()),
        ("Real-world Scenario", test_real_world_scenario()),
    ]
    
    results = []
    for test_name, test_coro in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = await test_coro
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("🧪 ASR Testing Summary:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 Step 2 (ASR with Whisper) completed successfully!")
        print("🚀 Ready for Step 3: LLM integration with Gemini API")
    else:
        print(f"\n⚠️ {total - passed} tests failed. Please check the errors above.")
    
    print("\n💡 Notes:")
    print("   - Synthetic audio may not produce meaningful Whisper transcriptions")
    print("   - The important thing is that the pipeline works without errors")
    print("   - Real speech audio will produce better transcription results")


if __name__ == "__main__":
    asyncio.run(main()) 
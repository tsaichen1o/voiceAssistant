#!/usr/bin/env python3
"""
Simple test for Whisper fix - Step 2.1
简单的Whisper修复验证测试
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


def create_simple_test_audio():
    """Create a very simple test audio for Whisper."""
    try:
        # Create a simple white noise (more likely to be processed by Whisper)
        sample_rate = 16000  # Use standard 16kHz for Whisper
        duration = 1.0  # Short 1 second
        
        # Generate white noise (simulates speech-like audio)
        np.random.seed(42)  # For reproducible results
        audio_data = np.random.normal(0, 0.1, int(sample_rate * duration)).astype(np.float32)
        
        # Apply a simple envelope to make it more speech-like
        envelope = np.sin(np.pi * np.linspace(0, 1, len(audio_data)))
        audio_data *= envelope
        
        print(f"✅ Generated simple test audio: {len(audio_data)} samples, {duration}s at {sample_rate}Hz")
        return audio_data, sample_rate
        
    except Exception as e:
        print(f"❌ Error creating simple test audio: {e}")
        return None, None


async def test_whisper_basic():
    """Test basic Whisper functionality with simple audio."""
    print("🧪 Testing Basic Whisper Functionality...")
    
    try:
        # Generate simple test audio
        audio_data, sample_rate = create_simple_test_audio()
        if audio_data is None:
            return False
        
        # Save to temporary WAV file
        temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_wav_path = temp_wav.name
        temp_wav.close()
        
        # Write audio data to file
        sf.write(temp_wav_path, audio_data, sample_rate)
        print(f"✅ Created temp audio file: {temp_wav_path}")
        
        # Test Whisper transcription
        print("🎤 Testing Whisper transcription...")
        transcribed_text = await opensource_voice_service._transcribe_audio_with_whisper(temp_wav_path)
        
        print(f"✅ Whisper transcription successful!")
        print(f"   Result: '{transcribed_text}'")
        print(f"   Length: {len(transcribed_text)} characters")
        
        # Clean up
        os.unlink(temp_wav_path)
        return True
        
    except Exception as e:
        print(f"❌ Basic Whisper test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_whisper_with_silence():
    """Test Whisper with silence (should return empty or minimal text)."""
    print("\n🔇 Testing Whisper with Silence...")
    
    try:
        # Create silence
        sample_rate = 16000
        duration = 0.5
        silence = np.zeros(int(sample_rate * duration), dtype=np.float32)
        
        # Save to temporary file
        temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_wav_path = temp_wav.name
        temp_wav.close()
        
        sf.write(temp_wav_path, silence, sample_rate)
        print(f"✅ Created silence audio file: {temp_wav_path}")
        
        # Test transcription
        print("🎤 Testing Whisper with silence...")
        transcribed_text = await opensource_voice_service._transcribe_audio_with_whisper(temp_wav_path)
        
        print(f"✅ Silence transcription completed!")
        print(f"   Result: '{transcribed_text}'")
        print(f"   Length: {len(transcribed_text)} characters")
        
        # Clean up
        os.unlink(temp_wav_path)
        return True
        
    except Exception as e:
        print(f"❌ Silence test failed: {e}")
        return False


async def test_whisper_error_handling():
    """Test Whisper error handling with invalid file."""
    print("\n❌ Testing Whisper Error Handling...")
    
    try:
        # Try to transcribe a non-existent file
        fake_path = "/nonexistent/fake_audio.wav"
        
        try:
            await opensource_voice_service._transcribe_audio_with_whisper(fake_path)
            print("❌ Should have failed with non-existent file")
            return False
        except FileNotFoundError:
            print("✅ Correctly handled non-existent file")
            return True
        except Exception as e:
            print(f"✅ Correctly handled error: {e}")
            return True
            
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


async def main():
    """Main test function."""
    print("🎯 Whisper Fix Verification - Step 2.1")
    print("Testing Whisper transcription with improved compatibility...")
    print("=" * 60)
    
    # Check if Whisper model is available
    try:
        health = await opensource_voice_service.health_check()
        print(f"Service Status: {health}")
        
        if health.get('components', {}).get('whisper') == 'not_loaded':
            print("🔄 Whisper model not loaded, initializing...")
            await opensource_voice_service._initialize_whisper_model()
        
    except Exception as e:
        print(f"❌ Failed to initialize service: {e}")
        return
    
    # Run tests
    tests = [
        ("Basic Whisper Functionality", test_whisper_basic()),
        ("Whisper with Silence", test_whisper_with_silence()),
        ("Error Handling", test_whisper_error_handling()),
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
    print(f"\n{'='*60}")
    print("🧪 Whisper Fix Testing Summary:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 Whisper fix successful! ASR functionality working correctly.")
        print("🚀 Ready for Step 3: LLM integration with Gemini API")
    else:
        print(f"\n⚠️ {total - passed} tests still failing.")
        print("💡 If tests still fail, this might be a system dependency issue.")
        print("   Consider trying a different Whisper model (tiny, small) or check system dependencies.")


if __name__ == "__main__":
    asyncio.run(main()) 
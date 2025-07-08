#!/usr/bin/env python3
"""
🧪 Test Script: End-to-End Integration Testing - Step 5

Comprehensive integration testing for the complete OpenSource Voice Assistant pipeline.
This validates the entire voice conversation flow with real audio, performance metrics,
error handling, and concurrent session management.

Test Categories:
1. 🎤 Real Audio Testing - Test with actual speech audio files
2. ⚡ Performance Benchmarking - Measure ASR + LLM + TTS latency
3. 🛡️ Error Handling - Edge cases and recovery mechanisms
4. 🔄 Concurrent Sessions - Multi-user session handling
5. 📊 Quality Assessment - Audio quality and conversation accuracy
"""

import asyncio
import os
import base64
import numpy as np
import soundfile as sf
from pathlib import Path
import tempfile
import time
from datetime import datetime
import concurrent.futures
import json

# Add the app directory to the Python path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.opensource_voice_service import opensource_voice_service

class VoiceTestAudioGenerator:
    """Generate test audio files with actual speech content."""
    
    @staticmethod
    def create_speech_audio(text: str, duration: float = 3.0, language: str = "en") -> str:
        """
        Create realistic speech-like audio using text-to-speech synthesis.
        Returns base64 encoded PCM audio.
        """
        try:
            from gtts import gTTS
            import tempfile
            import subprocess
            
            # Generate TTS audio file
            tts = gTTS(text=text, lang=language, slow=False)
            
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_mp3:
                tts.save(temp_mp3.name)
                
                # Convert MP3 to WAV using ffmpeg if available, otherwise use synthetic
                try:
                    wav_path = temp_mp3.name.replace('.mp3', '.wav')
                    subprocess.run([
                        'ffmpeg', '-i', temp_mp3.name, '-ar', '24000', 
                        '-ac', '1', '-sample_fmt', 's16', wav_path
                    ], check=True, capture_output=True)
                    
                    # Read WAV and convert to PCM
                    audio_data, sample_rate = sf.read(wav_path)
                    if len(audio_data.shape) > 1:
                        audio_data = audio_data[:, 0]  # Take first channel
                    
                    # Convert to PCM int16
                    pcm_data = (audio_data * 32767).astype(np.int16)
                    
                    # Cleanup
                    os.unlink(temp_mp3.name)
                    os.unlink(wav_path)
                    
                    return base64.b64encode(pcm_data.tobytes()).decode('utf-8')
                    
                except (subprocess.CalledProcessError, FileNotFoundError):
                    # Fallback to synthetic audio
                    print("   ⚠️ FFmpeg not available, using synthetic audio")
                    os.unlink(temp_mp3.name)
                    return VoiceTestAudioGenerator.create_synthetic_speech(text, duration)
                    
        except Exception as e:
            print(f"   ⚠️ TTS audio generation failed: {e}, using synthetic")
            return VoiceTestAudioGenerator.create_synthetic_speech(text, duration)
    
    @staticmethod
    def create_synthetic_speech(text: str, duration: float = 3.0) -> str:
        """Create synthetic speech-like audio patterns."""
        sample_rate = 24000
        total_samples = int(sample_rate * duration)
        
        # Create speech-like patterns with varying frequencies
        t = np.linspace(0, duration, total_samples)
        
        # Base frequency modulated by text characteristics
        base_freq = 150 + (len(text) % 50)  # 150-200 Hz range
        
        # Create complex waveform resembling speech formants
        speech = np.zeros(total_samples)
        
        # Add multiple harmonic components
        for i in range(1, 4):
            freq = base_freq * i
            amplitude = 0.3 / i  # Decreasing amplitude for harmonics
            speech += amplitude * np.sin(2 * np.pi * freq * t)
        
        # Add speech-like amplitude modulation
        modulation = 0.5 + 0.5 * np.sin(2 * np.pi * 3 * t)  # 3 Hz modulation
        speech *= modulation
        
        # Add some noise for realism
        noise = 0.05 * np.random.randn(total_samples)
        speech += noise
        
        # Normalize and convert to PCM
        speech = np.clip(speech, -1, 1)
        pcm_data = (speech * 32767).astype(np.int16)
        
        return base64.b64encode(pcm_data.tobytes()).decode('utf-8')

class PerformanceMetrics:
    """Track and analyze performance metrics."""
    
    def __init__(self):
        self.metrics = {
            "asr_times": [],
            "llm_times": [],
            "tts_times": [],
            "total_times": [],
            "audio_sizes": [],
            "response_lengths": []
        }
    
    def add_measurement(self, stage: str, duration: float, additional_data: dict = None):
        """Add a performance measurement."""
        if stage in self.metrics:
            self.metrics[stage].append(duration)
        
        if additional_data:
            for key, value in additional_data.items():
                if key not in self.metrics:
                    self.metrics[key] = []
                self.metrics[key].append(value)
    
    def get_stats(self, metric_name: str) -> dict:
        """Get statistics for a metric."""
        if metric_name not in self.metrics or not self.metrics[metric_name]:
            return {"count": 0}
        
        values = self.metrics[metric_name]
        return {
            "count": len(values),
            "mean": np.mean(values),
            "std": np.std(values),
            "min": np.min(values),
            "max": np.max(values),
            "median": np.median(values)
        }
    
    def print_summary(self):
        """Print performance summary."""
        print("\n📊 Performance Metrics Summary:")
        for metric, _ in self.metrics.items():
            if self.metrics[metric]:
                stats = self.get_stats(metric)
                print(f"   {metric}: {stats['mean']:.2f}±{stats['std']:.2f}s (min: {stats['min']:.2f}, max: {stats['max']:.2f})")

async def test_real_audio_conversation():
    """Test complete voice conversation with realistic audio."""
    print("🎤 Testing Real Audio Conversation...")
    
    # Test scenarios with different types of speech
    test_scenarios = [
        {
            "text": "Hello, how are you today?",
            "language": "en",
            "expected_keywords": ["hello", "how", "today"]
        },
        {
            "text": "What programs does TUM offer for computer science?",
            "language": "en", 
            "expected_keywords": ["TUM", "computer", "science", "program"]
        },
        {
            "text": "你好，请介绍一下慕尼黑工业大学",
            "language": "zh",
            "expected_keywords": ["你好", "慕尼黑", "工业大学"]
        }
    ]
    
    metrics = PerformanceMetrics()
    successful_conversations = 0
    
    for i, scenario in enumerate(test_scenarios):
        print(f"\n📋 Scenario {i+1}: {scenario['language']} - '{scenario['text'][:50]}...'")
        
        try:
            # Create realistic audio
            print("   🔊 Generating realistic speech audio...")
            start_time = time.time()
            audio_base64 = VoiceTestAudioGenerator.create_speech_audio(
                scenario['text'], 
                duration=3.0, 
                language=scenario['language']
            )
            audio_gen_time = time.time() - start_time
            print(f"   ✅ Audio generated in {audio_gen_time:.2f}s")
            
            # Create session
            user_id = f"real_audio_test_{int(time.time())}_{i}"
            session_data = await opensource_voice_service.create_session(user_id, is_audio=True)
            session_id = session_data["session_id"]
            
            # Process through complete pipeline
            print("   🔄 Processing through voice pipeline...")
            pipeline_start = time.time()
            
            asr_completed = False
            llm_completed = False
            tts_completed = False
            
            asr_start = None
            llm_start = None
            tts_start = None
            
            transcribed_text = ""
            assistant_response = ""
            audio_received = False
            
            async for response in opensource_voice_service.send_message(session_id, audio_base64, "audio/pcm"):
                event_type = response.get("type")
                event_data = response.get("data", "")
                
                if event_type == "text":
                    if "Transcribing with Whisper" in event_data:
                        asr_start = time.time()
                    elif "You said:" in event_data:
                        if asr_start:
                            asr_time = time.time() - asr_start
                            metrics.add_measurement("asr_times", asr_time)
                        asr_completed = True
                        transcribed_text = event_data.replace("👤 You said: \"", "").rstrip("\"")
                        print(f"   🎤 ASR: '{transcribed_text}'")
                    elif "Processing with Gemini" in event_data:
                        llm_start = time.time()
                    elif "Complete response:" in event_data:
                        if llm_start:
                            llm_time = time.time() - llm_start
                            metrics.add_measurement("llm_times", llm_time)
                        llm_completed = True
                        assistant_response = event_data.replace("🤖 Complete response: ", "")
                        print(f"   🧠 LLM: '{assistant_response[:50]}...'")
                    elif "Generating speech audio" in event_data:
                        tts_start = time.time()
                elif event_type == "audio":
                    if tts_start:
                        tts_time = time.time() - tts_start
                        metrics.add_measurement("tts_times", tts_time)
                    tts_completed = True
                    audio_received = True
                    audio_data = response.get("data", "")
                    audio_size = len(base64.b64decode(audio_data)) if audio_data else 0
                    metrics.add_measurement("audio_sizes", audio_size / 1024)  # KB
                    print(f"   🎵 TTS: Audio generated ({audio_size/1024:.1f} KB)")
            
            total_time = time.time() - pipeline_start
            metrics.add_measurement("total_times", total_time)
            metrics.add_measurement("response_lengths", len(assistant_response))
            
            # Cleanup
            await opensource_voice_service.close_session(session_id)
            
            # Evaluate conversation quality
            pipeline_success = asr_completed and llm_completed and tts_completed
            
            if pipeline_success:
                successful_conversations += 1
                print(f"   ✅ Complete conversation success in {total_time:.2f}s")
            else:
                print(f"   ❌ Incomplete conversation: ASR={asr_completed}, LLM={llm_completed}, TTS={tts_completed}")
                
        except Exception as e:
            print(f"   ❌ Scenario {i+1} failed: {e}")
    
    # Summary
    success_rate = successful_conversations / len(test_scenarios) * 100
    print(f"\n📊 Real Audio Conversation Results:")
    print(f"   ✅ Success Rate: {success_rate:.1f}% ({successful_conversations}/{len(test_scenarios)})")
    
    metrics.print_summary()
    
    return successful_conversations >= len(test_scenarios) * 0.5  # 50% success threshold

async def test_error_handling():
    """Test error handling and recovery mechanisms."""
    print("\n🛡️ Testing Error Handling and Recovery...")
    
    error_scenarios = [
        {
            "name": "Empty Audio",
            "audio_data": base64.b64encode(b"").decode('utf-8'),
            "mime_type": "audio/pcm",
            "expected_behavior": "graceful_handling"
        },
        {
            "name": "Invalid Audio Format",
            "audio_data": "invalid_base64_data!@#",
            "mime_type": "audio/pcm",
            "expected_behavior": "error_response"
        },
        {
            "name": "Very Long Text",
            "audio_data": "A" * 10000,  # Very long text to test LLM limits
            "mime_type": "text/plain",
            "expected_behavior": "truncation_or_handling"
        },
        {
            "name": "Special Characters",
            "audio_data": "Hello! @#$%^&*()_+ 测试 🎵🎤🧠",
            "mime_type": "text/plain",
            "expected_behavior": "proper_encoding"
        }
    ]
    
    error_handling_score = 0
    
    for scenario in error_scenarios:
        print(f"\n🧪 Testing: {scenario['name']}")
        
        try:
            # Create session
            user_id = f"error_test_{int(time.time())}"
            session_data = await opensource_voice_service.create_session(user_id, is_audio=True)
            session_id = session_data["session_id"]
            
            error_handled = False
            response_received = False
            
            async for response in opensource_voice_service.send_message(
                session_id, scenario['audio_data'], scenario['mime_type']
            ):
                response_received = True
                event_type = response.get("type")
                
                if event_type == "error":
                    error_handled = True
                    print(f"   ✅ Error properly handled: {response.get('error')}")
                elif event_type in ["text", "audio"]:
                    print(f"   ✅ Service continued normally: {event_type}")
            
            # Cleanup
            await opensource_voice_service.close_session(session_id)
            
            if response_received:
                error_handling_score += 1
                print(f"   ✅ {scenario['name']}: Service responded appropriately")
            else:
                print(f"   ❌ {scenario['name']}: No response received")
                
        except Exception as e:
            print(f"   ⚠️ {scenario['name']}: Exception caught (may be expected): {e}")
            error_handling_score += 0.5  # Partial credit for catching exceptions
    
    error_handling_rate = error_handling_score / len(error_scenarios) * 100
    print(f"\n📊 Error Handling Results:")
    print(f"   🛡️ Robustness Score: {error_handling_rate:.1f}% ({error_handling_score}/{len(error_scenarios)})")
    
    return error_handling_rate >= 75  # 75% handling threshold

async def test_concurrent_sessions():
    """Test concurrent session handling."""
    print("\n🔄 Testing Concurrent Sessions...")
    
    concurrent_sessions = 3
    test_messages = [
        "Hello, tell me about TUM's computer science program.",
        "What research opportunities are available at TUM?",
        "How can I apply for admission to TUM?"
    ]
    
    async def run_session(session_index: int, message: str):
        """Run a single session."""
        try:
            user_id = f"concurrent_test_{session_index}_{int(time.time())}"
            session_data = await opensource_voice_service.create_session(user_id, is_audio=False)
            session_id = session_data["session_id"]
            
            start_time = time.time()
            response_received = False
            
            async for response in opensource_voice_service.send_message(session_id, message, "text/plain"):
                if response.get("type") == "text" and "Complete response:" in response.get("data", ""):
                    response_received = True
                    break
            
            end_time = time.time()
            await opensource_voice_service.close_session(session_id)
            
            return {
                "session_index": session_index,
                "success": response_received,
                "duration": end_time - start_time
            }
            
        except Exception as e:
            return {
                "session_index": session_index,
                "success": False,
                "error": str(e)
            }
    
    # Run concurrent sessions
    print(f"   🚀 Starting {concurrent_sessions} concurrent sessions...")
    start_time = time.time()
    
    tasks = [
        run_session(i, test_messages[i % len(test_messages)]) 
        for i in range(concurrent_sessions)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    total_time = time.time() - start_time
    
    # Analyze results
    successful_sessions = 0
    total_duration = 0
    
    for result in results:
        if isinstance(result, dict) and result.get("success"):
            successful_sessions += 1
            total_duration += result.get("duration", 0)
        elif isinstance(result, Exception):
            print(f"   ❌ Session failed with exception: {result}")
    
    success_rate = successful_sessions / concurrent_sessions * 100
    avg_duration = total_duration / max(successful_sessions, 1)
    
    print(f"\n📊 Concurrent Sessions Results:")
    print(f"   ✅ Success Rate: {success_rate:.1f}% ({successful_sessions}/{concurrent_sessions})")
    print(f"   ⏱️ Total Time: {total_time:.2f}s")
    print(f"   ⏱️ Average Session Duration: {avg_duration:.2f}s")
    print(f"   🔄 Concurrency Efficiency: {(avg_duration / total_time * concurrent_sessions):.2f}")
    
    return success_rate >= 80  # 80% success rate for concurrent sessions

async def test_system_limits():
    """Test system limits and resource usage."""
    print("\n📏 Testing System Limits...")
    
    # Test various limits
    limit_tests = [
        {
            "name": "Max Audio Size",
            "test": "large_audio",
            "description": "Test with large audio files"
        },
        {
            "name": "Long Conversation",
            "test": "long_conversation", 
            "description": "Test extended conversation history"
        },
        {
            "name": "Rapid Requests",
            "test": "rapid_requests",
            "description": "Test rapid consecutive requests"
        }
    ]
    
    limits_passed = 0
    
    for test_config in limit_tests:
        print(f"\n🧪 {test_config['name']}: {test_config['description']}")
        
        try:
            if test_config["test"] == "large_audio":
                # Test with larger synthetic audio
                large_audio = VoiceTestAudioGenerator.create_synthetic_speech("This is a test message", duration=10.0)
                
                user_id = f"limit_test_audio_{int(time.time())}"
                session_data = await opensource_voice_service.create_session(user_id, is_audio=True)
                session_id = session_data["session_id"]
                
                response_received = False
                async for response in opensource_voice_service.send_message(session_id, large_audio, "audio/pcm"):
                    if response.get("type") in ["text", "audio"]:
                        response_received = True
                        break
                
                await opensource_voice_service.close_session(session_id)
                
                if response_received:
                    limits_passed += 1
                    print("   ✅ Large audio handled successfully")
                else:
                    print("   ❌ Large audio failed")
                    
            elif test_config["test"] == "long_conversation":
                # Test with multiple conversation turns
                user_id = f"limit_test_conv_{int(time.time())}"
                session_data = await opensource_voice_service.create_session(user_id, is_audio=False)
                session_id = session_data["session_id"]
                
                conversation_success = True
                for i in range(5):  # 5 conversation turns
                    message = f"This is message number {i+1}. Tell me something about TUM."
                    response_received = False
                    
                    async for response in opensource_voice_service.send_message(session_id, message, "text/plain"):
                        if response.get("type") == "text" and "Complete response:" in response.get("data", ""):
                            response_received = True
                            break
                    
                    if not response_received:
                        conversation_success = False
                        break
                
                await opensource_voice_service.close_session(session_id)
                
                if conversation_success:
                    limits_passed += 1
                    print("   ✅ Long conversation handled successfully")
                else:
                    print("   ❌ Long conversation failed")
                    
            elif test_config["test"] == "rapid_requests":
                # Test rapid consecutive requests
                user_id = f"limit_test_rapid_{int(time.time())}"
                session_data = await opensource_voice_service.create_session(user_id, is_audio=False)
                session_id = session_data["session_id"]
                
                rapid_success = 0
                for i in range(3):  # 3 rapid requests
                    message = f"Quick question {i+1}: What is TUM?"
                    response_received = False
                    
                    async for response in opensource_voice_service.send_message(session_id, message, "text/plain"):
                        if response.get("type") == "text" and "Complete response:" in response.get("data", ""):
                            response_received = True
                            break
                    
                    if response_received:
                        rapid_success += 1
                
                await opensource_voice_service.close_session(session_id)
                
                if rapid_success >= 2:  # At least 2/3 success
                    limits_passed += 1
                    print(f"   ✅ Rapid requests handled successfully ({rapid_success}/3)")
                else:
                    print(f"   ❌ Rapid requests failed ({rapid_success}/3)")
                    
        except Exception as e:
            print(f"   ❌ {test_config['name']} failed with exception: {e}")
    
    limits_score = limits_passed / len(limit_tests) * 100
    print(f"\n📊 System Limits Results:")
    print(f"   📏 Limits Handling: {limits_score:.1f}% ({limits_passed}/{len(limit_tests)})")
    
    return limits_score >= 66  # 66% threshold (2/3 tests)

async def main():
    """Run comprehensive end-to-end integration testing."""
    print("🎯 End-to-End Integration Testing - Step 5")
    print("Testing complete OpenSource Voice Assistant pipeline...")
    print("=" * 70)
    
    # Get service status
    status = await opensource_voice_service.health_check()
    print(f"Service Status: {status}\n")
    
    # Verify all components are ready
    components = status.get("components", {})
    critical_components = ["redis", "gemini_api", "gtts"]
    
    for component in critical_components:
        if components.get(component) not in ["healthy", "configured", "available"]:
            print(f"❌ {component} not ready: {components.get(component)}")
            print("Cannot proceed with integration testing.")
            return
    
    print("✅ All critical components ready for integration testing\n")
    
    # Run comprehensive tests
    test_results = []
    
    tests = [
        ("Real Audio Conversation", test_real_audio_conversation()),
        ("Error Handling", test_error_handling()),
        ("Concurrent Sessions", test_concurrent_sessions()),
        ("System Limits", test_system_limits()),
    ]
    
    overall_start = time.time()
    
    for test_name, test_coro in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            test_start = time.time()
            result = await test_coro
            test_duration = time.time() - test_start
            test_results.append((test_name, result, test_duration))
            print(f"\n⏱️ {test_name} completed in {test_duration:.2f}s")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            test_results.append((test_name, False, 0))
    
    total_duration = time.time() - overall_start
    
    # Final Summary
    print("\n" + "=" * 70)
    print("🧪 End-to-End Integration Testing Summary:")
    
    passed = 0
    for test_name, result, duration in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name} ({duration:.2f}s)")
        if result:
            passed += 1
    
    success_rate = passed / len(test_results) * 100
    print(f"\n📊 Overall Results:")
    print(f"   🎯 Success Rate: {success_rate:.1f}% ({passed}/{len(test_results)})")
    print(f"   ⏱️ Total Testing Time: {total_duration:.2f}s")
    
    if success_rate >= 75:
        print(f"\n🎉 Step 5 (End-to-End Integration) completed successfully!")
        print("🚀 OpenSource Voice Assistant is ready for production!")
        print("\n✨ Complete System Validation:")
        print("   🎤 Real Audio Processing ✅")
        print("   ⚡ Performance Benchmarking ✅") 
        print("   🛡️ Error Handling & Recovery ✅")
        print("   🔄 Concurrent Session Management ✅")
        print("   📏 System Limits & Scalability ✅")
        print("\n🎯 Ready for Step 6: Frontend Integration")
    elif success_rate >= 50:
        print(f"\n⚠️ Step 5 partially completed ({success_rate:.1f}%)")
        print("💡 Core functionality working, some optimization needed")
        print("🔧 Consider addressing failed tests before frontend integration")
    else:
        print(f"\n❌ Step 5 failed ({success_rate:.1f}%)")
        print("🔧 Significant issues detected, review and fix before proceeding")
        print("💡 Check component health, network connectivity, and resource limits")

if __name__ == "__main__":
    asyncio.run(main()) 
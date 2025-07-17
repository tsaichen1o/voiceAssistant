#!/usr/bin/env python3
"""
Test specifically for upload completion to audio response time
"""

import asyncio
import aiohttp
import time
import os
import base64
import json
from dotenv import load_dotenv
import jwt

# Load environment variables
load_dotenv()

API_URL = os.getenv('API_URL', 'http://localhost:8000')
AUTH_TOKEN = os.getenv('AUTH_TOKEN')

if not AUTH_TOKEN:
    print("Please set AUTH_TOKEN in your .env file")
    exit(1)

# Extract user_id from JWT token
try:
    decoded_token = jwt.decode(AUTH_TOKEN, options={"verify_signature": False})
    USER_ID = decoded_token.get('sub')
    if not USER_ID:
        print("Could not extract user_id from JWT token")
        exit(1)
    print(f"Using User ID: {USER_ID}")
except Exception as e:
    print(f"Error decoding JWT token: {e}")
    exit(1)

async def test_upload_to_response_time():
    """Test specifically for upload completion to audio response time"""
    
    # Check if the converted PCM file exists
    audio_file_path = "TestAudio.pcm"
    if not os.path.exists(audio_file_path):
        print(f"PCM file {audio_file_path} not found!")
        m4a_file = "TestAudio.m4a"
        if os.path.exists(m4a_file):
            print(f"Found M4A file {m4a_file}, but we need PCM format.")
            print("Please run: python convert_audio.py")
        return
    
    # Read the audio file
    with open(audio_file_path, 'rb') as f:
        audio_data = f.read()
    
    print(f"Loaded audio file: {len(audio_data)} bytes")
    print("🎯 Test Target: Measure upload completion to audio response time")
    
    session = aiohttp.ClientSession()
    try:
        # Step 1: Establish SSE connection and get session_id
        print("\n=== Establishing connection and getting session_id ===")
        
        headers = {
            'Authorization': f'Bearer {AUTH_TOKEN}',
            'Accept': 'text/event-stream',
            'Cache-Control': 'no-cache'
        }
        
        sse_response = await session.get(
            f'{API_URL}/api/voice-redis/events/{USER_ID}?is_audio=true',
            headers=headers
        )
        
        if sse_response.status != 200:
            print(f"Failed to connect to SSE: {sse_response.status}")
            return
        
        # Get session_id from first event
        session_id = None
        async for line in sse_response.content:
            line = line.decode('utf-8').strip()
            if line.startswith('data: '):
                data = line[6:]
                try:
                    event_data = json.loads(data)
                    if 'session_id' in event_data and 'session_created' in data:
                        session_id = event_data.get('session_id')
                        print(f"✅ Got session_id: {session_id}")
                        break
                except json.JSONDecodeError:
                    continue
        
        if not session_id:
            print("❌ Could not get session_id")
            return
        
        # Step 2: Upload audio and start timing
        print(f"\n=== Starting precise timing test ===")
        print("📤 Uploading audio...")
        
        # Convert audio to base64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        message_data = {
            "mime_type": "audio/pcm",
            "data": audio_base64
        }
        
        send_url = f"{API_URL}/api/voice-redis/send/{session_id}"
        
        upload_response = await session.post(
            send_url,
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'},
            json=message_data
        )
        
        if upload_response.status != 200:
            print(f"❌ Audio upload failed: {upload_response.status}")
            return
        
        # 🎯 Key timing point: Upload complete, start timer
        upload_complete_time = time.time()
        print(f"✅ Audio upload complete, timing started!")
        
        # Read upload confirmation
        async for line in upload_response.content:
            line = line.decode('utf-8').strip()
            if line.startswith('data: '):
                try:
                    data = json.loads(line[6:])
                    print(f"📤 Upload confirmation: {data.get('type', 'unknown')}")
                except json.JSONDecodeError:
                    pass
                break
        
        # Step 3: Listen specifically for audio response
        print("🔍 Waiting for audio response...")
        
        audio_response_time = None
        timeout = 20  # 20 second timeout
        
        async for line in sse_response.content:
            line = line.decode('utf-8').strip()
            current_time = time.time()
            
            # Check timeout
            if current_time - upload_complete_time > timeout:
                print(f"⏰ Timeout after {timeout}s, no audio response received")
                break
            
            if line.startswith('data: '):
                data = line[6:]
                elapsed = current_time - upload_complete_time
                
                try:
                    event_data = json.loads(data)
                    event_type = event_data.get('type', 'unknown')
                    
                    if event_type == 'text':
                        text_content = event_data.get('data', '')[:50]
                        print(f"📝 Text response ({elapsed:.2f}s): {text_content}...")
                    
                    elif event_type == 'audio':
                        # 🎯 Key timing point: Audio response received
                        audio_response_time = current_time
                        audio_size = len(event_data.get('data', ''))
                        processing_time = audio_response_time - upload_complete_time
                        
                        print(f"🎵 Audio response received!")
                        print(f"⏱️  Processing time: {processing_time:.2f}s")
                        print(f"📊 Audio size: {audio_size} bytes")
                        break
                    
                    elif event_type == 'control':
                        turn_complete = event_data.get('turn_complete', False)
                        if turn_complete:
                            if audio_response_time:
                                print(f"✅ Processing completion confirmed")
                                break
                            else:
                                print(f"⚠️  Processing complete but no audio response received")
                                break
                    
                    elif event_type == 'error':
                        error_msg = event_data.get('message', 'Unknown error')
                        print(f"❌ Error: {error_msg}")
                        break
                    
                    else:
                        print(f"📡 Event ({elapsed:.2f}s): {event_type}")
                
                except json.JSONDecodeError:
                    print(f"📡 Raw event ({elapsed:.2f}s): {data[:100]}...")
        
        # Final results
        print(f"\n=== Test Results ===")
        print(f"📁 Audio file: {audio_file_path} ({len(audio_data)} bytes)")
        
        if audio_response_time:
            processing_time = audio_response_time - upload_complete_time
            print(f"🎯 Upload completion to audio response time: {processing_time:.2f}s")
            print(f"✅ Test successful!")

            
        else:
            print(f"❌ No audio response received")
            print(f"🔍 Suggest checking backend processing pipeline")
    
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await session.close()

if __name__ == "__main__":
    print("🎯 Specialized Test: Upload completion to audio response time")
    print("=" * 50)
    asyncio.run(test_upload_to_response_time()) 
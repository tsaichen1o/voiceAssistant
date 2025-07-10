import os
import json
import base64
import asyncio
import redis.asyncio as redis
from typing import Dict, Optional, AsyncGenerator, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv
import numpy as np
import io
import soundfile as sf
import tempfile

# TODO : remove the ADK with direct Gemini API calls and local voice models

from app.config import settings

import os
import torch
from TTS.api import TTS
import whisper
from faster_whisper import WhisperModel

import collections
os.environ["PATH"] += os.pathsep + r"C:\Users\huhan\App\ffmpeg\bin"

from torch.serialization import add_safe_globals
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import XttsAudioConfig, XttsArgs
from TTS.config.shared_configs import BaseDatasetConfig
add_safe_globals([collections.defaultdict])
add_safe_globals([dict])

add_safe_globals([XttsConfig, XttsAudioConfig, BaseDatasetConfig, XttsArgs])

from TTS.utils.radam import RAdam

add_safe_globals([RAdam])
os.environ["TRANSFORMERS_TRUST_REMOTE_CODE"] = "true"

device = "cuda" if torch.cuda.is_available() else "cpu"

# asr_model = whisper.load_model("large-v2", device=device)
asr_model = WhisperModel("base", device=device, compute_type="float32")
transcribe_audio = asr_model.transcribe
tts_model = TTS(model_name=settings.VOICE_MODEL, progress_bar=False)

def synthesize_speech(text: str) -> bytes:
    # 1. 合成语音波形
    waveform = tts_model.tts(text)

    # 2. 写入内存 buffer，保存为 WAV 格式
    buf = io.BytesIO()
    sf.write(buf, waveform, samplerate=tts_model.synthesizer.output_sample_rate, format="WAV")
    buf.seek(0)

    # 3. 返回 bytes 数据，用于 base64 编码
    return buf.read()

# Load environment variables
load_dotenv()

APP_NAME = "Voice Assistant"
SESSION_EXPIRY = 3600  # 1 hour
# SESSION_EXPIRY = 3600  # 1 hour 
SAMPLE_RATE = 16000
BUFFER_SECONDS = 1.5

class RedisVoiceService:
    """Voice service using Redis for session state management but ADK for voice processing."""
    
    def __init__(self):
        """Initialize the Redis-based voice service with ADK integration."""
        # Initialize Redis connection for session management
        if hasattr(settings, 'REDIS_URL') and settings.REDIS_URL:
            self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=False)
        else:
            self.redis_client = redis.Redis(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                password=getattr(settings, 'REDIS_PASSWORD', None),
                decode_responses=False
            )
        self.audio_buffer: Dict[str, list] = {}  # per-session audio buffer
    
    async def create_session(self, user_id: str, is_audio: bool = True) -> Dict[str, Any]:
        """
        Create a new voice session with Redis state management and ADK voice processing.
        
        Args:
            user_id: Unique identifier for the user
            is_audio: Whether to use audio mode (default: True)
            
        Returns:
            Session information dictionary
        """
        try:
            session_id = f"voice_{user_id}_{int(datetime.now().timestamp())}"
            
            # Create session data for Redis
            session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "is_audio": is_audio,
                "created_at": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat(),
                "status": "active",
                "conversation_history": []
            }
            
            # Store in Redis with expiration
            redis_key = f"voice_session:{session_id}"
            session_json = json.dumps(session_data)
            print(f"🔍 Storing session in Redis key: {redis_key}, data length: {len(session_json)}")
            await self.redis_client.setex(
                redis_key,
                SESSION_EXPIRY,
                session_json
            )
            
            # Verify the session was stored
            stored_data = await self.redis_client.get(redis_key)
            if stored_data:
                print(f"✅ Session successfully stored and verified in Redis")
            else:
                print(f"❌ Failed to store session in Redis!")
            
            print(f"✅ Created voice session: {session_id} for user: {user_id}")
            return session_data
            
        except Exception as e:
            print(f"❌ Error creating Redis voice session: {e}")
            raise

    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from Redis."""
        try:
            redis_key = f"voice_session:{session_id}"
            print(f"🔍 Getting session from Redis key: {redis_key}")
            session_data = await self.redis_client.get(redis_key)
            if session_data:
                print(f"✅ Found session data in Redis: {len(session_data)} bytes")
                return json.loads(session_data.decode('utf-8'))
            else:
                print(f"❌ No data found for Redis key: {redis_key}")
            return None
        except Exception as e:
            print(f"❌ Error getting session from Redis: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def update_session(self, session_id: str, update_data: Dict[str, Any]) -> bool:
        """Update session data in Redis."""
        try:
            session_data = await self.get_session(session_id)
            if not session_data:
                return False
            
            # Update the data
            session_data.update(update_data)
            session_data["last_active"] = datetime.now().isoformat()
            
            # Save back to Redis
            await self.redis_client.setex(
                f"voice_session:{session_id}",
                SESSION_EXPIRY,
                json.dumps(session_data)
            )
            return True
        except Exception as e:
            print(f"❌ Error updating session in Redis: {e}")
            return False
    
    async def send_message(self, session_id: str, content: str, mime_type: str = "text/plain") -> AsyncGenerator[Dict[str, Any], None]:
        """
        Send a message and stream the response using ADK for audio or direct Gemini for text.
        
        Args:
            session_id: Session identifier
            content: Message content (text or base64 audio)
            mime_type: Content type
            
        Yields:
            Response events from the agent
        """
        try:
            print(f"🔍 Looking for session: {session_id}")
            session_data = await self.get_session(session_id)
            if not session_data:
                print(f"❌ Session {session_id} not found in Redis")
                # List all active sessions for debugging
                all_sessions = await self.list_active_sessions()
                print(f"🔍 Active sessions: {all_sessions}")
                yield {"type": "error", "message": "Session not found"}
                return
            
            print(f"✅ Found session: {session_id}, audio mode: {session_data.get('is_audio', False)}")
            
            if mime_type == "audio/pcm":
                print(f"[REDIS VOICE] Audio message: {len(content)} chars (base64)")
                audio_bytes = base64.b64decode(content)
                audio_np_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                self.audio_buffer.setdefault(session_id, []).extend(audio_np_array.tolist())


            # 兼容前端，先发 status
                yield {
                    "type": "status",
                    "session_id": session_id,
                    "message": "Audio data received",
                    "bytes_sent": len(audio_bytes)
                }
                # Check buffer length
                buffer = np.array(self.audio_buffer[session_id], dtype=np.float32)
                if len(buffer) >= int(SAMPLE_RATE * BUFFER_SECONDS):
                    # transcript = transcribe_audio(buffer)
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
                        sf.write(tmp_wav.name, buffer, SAMPLE_RATE)
                        transcript = transcribe_audio(tmp_wav.name)
                        # transcript_text = transcript.get("text", "") if isinstance(transcript, dict) else transcript
                    # self.audio_buffer[session_id] = []

                    # Extract transcription + language  
                    if isinstance(transcript, dict):
                        transcript_text = transcript.get("text", "")
                        transcript_lang = transcript.get("language", "en")
                    else:
                        transcript_text = transcript
                        transcript_lang = "en"

                    yield {
                        "type": "transcript",
                        "session_id": session_id,
                        "data": {
                            "text": transcript_text,
                            "language": transcript_lang,
                            "inline_data": None
                        },
                        "partial": False
                    }

                    async for event in self._process_text_with_gemini(session_data, transcript_text):
                        yield event
                        if event["type"] == "text" and not event.get("partial", False):
                            audio_out = synthesize_speech(event["data"])
                            yield {
                                "type": "audio",
                                "session_id": session_id,
                                "mime_type": "audio/wav",
                                "data": base64.b64encode(audio_out).decode("utf-8")
                            }
                                # Clear audio buffer
                    self.audio_buffer[session_id] = []
                    
            elif mime_type == "text/plain":
                print(f"[REDIS VOICE] Text message:  {content}")
                
                async for event in self._process_text_with_gemini(session_data, content):
                    yield event
                    if event["type"] == "text" and not event.get("partial", False):
                        audio_out = synthesize_speech(event["data"])
                        yield {
                            "type": "audio",
                            "mime_type": "audio/wav",
                            "data": base64.b64encode(audio_out).decode("utf-8")
                        }
            else:
                yield {"type": "error", "message": f"Unsupported mime_type: {mime_type}"}
            
        except Exception as e:
            print(f"❌ Error in Redis voice processing: {e}")
            yield {"type": "error", "message": str(e)}
    
    async def _process_text_with_gemini(self, session_data: Dict[str, Any], content: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Process text messages using direct Gemini API."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            
            history = session_data.get("conversation_history", [])
            
            try:
                model = genai.GenerativeModel(
                    model_name=settings.VOICE_MODEL,
                    system_instruction="You are a helpful voice assistant. Respond naturally and helpfully to user queries. Keep responses conversational and engaging."
                )
            except Exception as e:
                print(f"⚠️ Voice model {settings.VOICE_MODEL} failed, falling back to {settings.GEMINI_MODEL}: {e}")
                model = genai.GenerativeModel(
                    model_name=settings.GEMINI_MODEL,
                    system_instruction="You are a helpful voice assistant. Respond naturally and helpfully to user queries. Keep responses conversational and engaging."
                )
            
            chat = model.start_chat(history=[
                {"role": msg["role"], "parts": [msg["content"]]} 
                for msg in history
            ])
            
            response = chat.send_message(content, stream=True)
            
            full_response = ""
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    yield {
                        "type": "text",
                        "data": chunk.text,
                        "partial": True
                    }
            
            yield {
                "type": "text", 
                "data": full_response,
                "partial": False
            }
            
            history.append({"role": "user", "content": content})
            history.append({"role": "model", "content": full_response})
            await self.update_session(session_data["session_id"], {"conversation_history": history})
            
        except Exception as e:
            print(f"❌ Error in Gemini text processing: {e}")
            yield {"type": "error", "message": str(e)}
    
    async def close_session(self, session_id: str) -> bool:
        """
        Close a voice session and clean up ADK resources.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful
        """
        try:
            await self.redis_client.delete(f"voice_session:{session_id}")
            print(f"✅ Closed voice session: {session_id}")
            return True
        except Exception as e:
            print(f"❌ Error closing session: {e}")
            return False
    
    async def list_active_sessions(self) -> list[str]:
        """Get list of active session IDs."""
        try:
            keys = await self.redis_client.keys("voice_session:*")
            return [key.decode('utf-8').replace("voice_session:", "") for key in keys]
        except Exception as e:
            print(f"❌ Error listing sessions: {e}")
            return []


# Create a global instance
redis_voice_service = RedisVoiceService() 
import os
import json
import base64
import asyncio
import numpy as np
import tempfile
import soundfile as sf
import redis.asyncio as redis
from typing import Dict, Optional, AsyncGenerator, Any
from datetime import datetime
from dotenv import load_dotenv

from faster_whisper import WhisperModel
from app.config import settings
import io
import logging

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

tts_model = TTS(model_name="tts_models/en/ljspeech/tacotron2-DCA", progress_bar=False)

def synthesize_speech(text: str) -> bytes:
    # 1. 合成语音波形
    waveform = tts_model.tts(text)

    # 2. 写入内存 buffer，保存为 WAV 格式
    buf = io.BytesIO()
    sf.write(buf, waveform, samplerate=tts_model.synthesizer.output_sample_rate, format="WAV")
    buf.seek(0)

    # 3. 返回 bytes 数据，用于 base64 编码
    return buf.read()
def safe_synthesize_speech(text: str) -> Optional[bytes]:
    """
    合成语音，自动跳过过短、非法或 emoji-only 的文本，防止 TTS 报错。
    返回 None 表示跳过该句。
    """
    cleaned_text = text.strip()
    
    # ✅ 跳过空字符串或无意义的符号
    if not cleaned_text or len(cleaned_text) < 5 or not any(c.isalnum() for c in cleaned_text):
        logging.warning(f"⏩ Skipping TTS: content too short or non-verbal → '{cleaned_text}'")
        return None

    # ✅ 可选：过滤掉 emoji 和特殊字符（只保留常用标点）
    cleaned_text = re.sub(r"[^\w\s.,!?'\"]+", '', cleaned_text)

    try:
        return synthesize_speech(cleaned_text)
    except Exception as e:
        logging.error(f"❌ TTS synthesis failed for: '{cleaned_text}' → {e}")
        return None

load_dotenv()

APP_NAME = "Voice Assistant"
SESSION_EXPIRY = 3600  # 1 hour 
SAMPLE_RATE = 16000
BUFFER_SECONDS = 1.5

# Initialize faster-whisper once
whisper_model = WhisperModel("large-v2", compute_type="float32")

class RedisVoiceService:
    def __init__(self):
        if hasattr(settings, 'REDIS_URL') and settings.REDIS_URL:
            self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=False)
        else:
            self.redis_client = redis.Redis(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                password=getattr(settings, 'REDIS_PASSWORD', None),
                decode_responses=False
            )
        self.audio_buffer: Dict[str, list] = {}

    async def create_session(self, user_id: str, is_audio: bool = True) -> Dict[str, Any]:
        session_id = f"voice_{user_id}_{int(datetime.now().timestamp())}"
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "is_audio": is_audio,
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "status": "active",
            "conversation_history": []
        }
        redis_key = f"voice_session:{session_id}"
        await self.redis_client.setex(redis_key, SESSION_EXPIRY, json.dumps(session_data))
        self.audio_buffer[session_id] = []
        return session_data

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        redis_key = f"voice_session:{session_id}"
        session_data = await self.redis_client.get(redis_key)
        if session_data:
            return json.loads(session_data.decode('utf-8'))
        return None

    async def update_session(self, session_id: str, update_data: Dict[str, Any]) -> bool:
        session_data = await self.get_session(session_id)
        if not session_data:
            return False
        session_data.update(update_data)
        session_data["last_active"] = datetime.now().isoformat()
        await self.redis_client.setex(
            f"voice_session:{session_id}",
            SESSION_EXPIRY,
            json.dumps(session_data)
        )
        return True

    async def send_message(self, session_id: str, content: str, mime_type: str = "audio/pcm") -> AsyncGenerator[Dict[str, Any], None]:
        try:
            # ✅ 校验空 content
            if not content or not isinstance(content, str) or content.strip() == "":
                yield {"type": "error", "message": "'content' must not be empty."}
                return

            session_data = await self.get_session(session_id)
            if not session_data:
                yield {"type": "error", "message": "Session not found"}
                return

            if mime_type == "audio/pcm":
                try:
                    audio_bytes = base64.b64decode(content)
                except Exception:
                    yield {"type": "error", "message": "Failed to decode base64 audio."}
                    return

                if len(audio_bytes) < 512:  # ✅ 防止无效音频
                    yield {"type": "error", "message": "Audio data too short."}
                    return

                audio_np_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                self.audio_buffer.setdefault(session_id, []).extend(audio_np_array.tolist())

                yield {
                    "type": "status",
                    "session_id": session_id,
                    "message": "Audio data received",
                    "bytes_sent": len(audio_bytes)
                }

                buffer = np.array(self.audio_buffer[session_id], dtype=np.float32)
                if len(buffer) >= int(SAMPLE_RATE * BUFFER_SECONDS):
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
                        sf.write(tmp_wav.name, buffer, SAMPLE_RATE)

                    # ✅ 防御性调用 whisper
                    try:
                        segments, info = whisper_model.transcribe(tmp_wav.name, beam_size=5)
                    except Exception as e:
                        yield {"type": "error", "message": f"Whisper error: {str(e)}"}
                        return

                    transcript_text = "".join([seg.text for seg in segments])
                    transcript_lang = info.language if info else "en"

                    if not transcript_text.strip():
                        yield {"type": "error", "message": "No speech detected."}
                        return

                    yield {
                        "type": "transcript",
                        "session_id": session_id,
                        "data": {
                            "text": transcript_text.strip(),
                            "language": transcript_lang,
                            "inline_data": None
                        },
                        "partial": False
                    }

                    # ✅ Gemini流式输出
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

                    self.audio_buffer[session_id] = []

            elif mime_type == "text/plain":
                if not content.strip():
                    yield {"type": "error", "message": "Text content is empty."}
                    return

                async for event in self._process_text_with_gemini(session_data, content):
                    yield event
                    if event["type"] == "text" and not event.get("partial", False):
                        audio_out = safe_synthesize_speech(event["data"])
                        if audio_out:
                            yield {
                                "type": "audio",
                                "session_id": session_id,
                                "mime_type": "audio/wav",
                                "data": base64.b64encode(audio_out).decode("utf-8")
                            }
                        

            else:
                yield {"type": "error", "message": f"Unsupported mime_type: {mime_type}"}

        except Exception as e:
            print(f"❌ Error in send_message: {e}")
            yield {"type": "error", "message": str(e)}


    async def _process_text_with_gemini(self, session_data: Dict[str, Any], content: str) -> AsyncGenerator[Dict[str, Any], None]:
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)

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
        try:
            await self.redis_client.delete(f"voice_session:{session_id}")
            self.audio_buffer.pop(session_id, None)
            print(f"✅ Closed voice session: {session_id}")
            return True
        except Exception as e:
            print(f"❌ Error closing session: {e}")
            return False

    async def list_active_sessions(self) -> list[str]:
        try:
            keys = await self.redis_client.keys("voice_session:*")
            return [key.decode('utf-8').replace("voice_session:", "") for key in keys]
        except Exception as e:
            print(f"❌ Error listing sessions: {e}")
            return []


# Create a global instance
redis_voice_service = RedisVoiceService()

import os
import re
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
from google.generativeai.client import configure
from google.generativeai.generative_models import GenerativeModel
from app.config import settings

# Rmemainder: comment the VOICE_MODEL line in .env file

# Ensure ffmpeg is in the PATH for soundfile to work correctly
# If it is already set in your environment, this line can be removed
os.environ["PATH"] += os.pathsep + r"C:\Users\huhan\App\ffmpeg\bin"

from app.services.asr import transcribe
from app.services.tts import safe_synthesize_speech

load_dotenv()

APP_NAME = "Voice Assistant"
SESSION_EXPIRY = 3600  # 1 hour 
SAMPLE_RATE = 16000
BUFFER_SECONDS = 4

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
            # ✅ content validation
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

                # if len(audio_bytes) < 512:  # ✅ Minimum length check
                #     yield {"type": "error", "message": "Audio data too short."}
                #     return

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

                    # import fast whisper
                    try:
                        transcript_text, transcript_lang = transcribe(buffer, sample_rate=SAMPLE_RATE)
                    except Exception as e:
                        yield {"type": "error", "message": f"Whisper error: {str(e)}"}
                        return

                    # if not transcript_text.strip():
                    #     yield {"type": "error", "message": "No speech detected."}
                    #     return

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

                    # ✅ Gemini AI text processing
                    async for event in self._process_text_with_gemini(session_data, transcript_text):
                        yield event
                        
                    self.audio_buffer[session_id] = []

            elif mime_type == "text/plain":
                if not content.strip():
                    yield {"type": "error", "message": "Text content is empty."}
                    return

                async for event in self._process_text_with_gemini(session_data, content):
                    yield event

            else:
                yield {"type": "error", "message": f"Unsupported mime_type: {mime_type}"}

        except Exception as e:
            print(f"❌ Error in send_message: {e}")
            yield {"type": "error", "message": str(e)}


    # TODO: Add Vertex AI Search integration
    async def _process_text_with_gemini(self, session_data: Dict[str, Any], content: str) -> AsyncGenerator[Dict[str, Any], None]:
        from google.api_core.client_options import ClientOptions
        from google.cloud import discoveryengine_v1 as discoveryengine
        from google.generativeai.types import GenerationConfig
        try:
            configure(api_key=settings.GEMINI_API_KEY)
            # history = session_data.get("conversation_history", [])

            # ========== 1. Vertex AI Search ==========
            project_id = settings.VERTEX_AI_SEARCH_PROJECT_ID
            location = settings.VERTEX_AI_SEARCH_LOCATION
            engine_id = settings.VERTEX_AI_SEARCH_ENGINE_ID
            client_options = (
                ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
                if location != "global" else None
            )
            client = discoveryengine.SearchServiceClient(client_options=client_options)
            serving_config = f"projects/{project_id}/locations/{location}/collections/default_collection/engines/{engine_id}/servingConfigs/default_config"

            content_search_spec = discoveryengine.SearchRequest.ContentSearchSpec(
                summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                    summary_result_count=5,
                    include_citations=False,
                    ignore_adversarial_query=True,
                    ignore_non_summary_seeking_query=True,
                )
            )

            request = discoveryengine.SearchRequest(
                serving_config=serving_config,
                query=content,
                page_size=10,
                content_search_spec=content_search_spec,
                spell_correction_spec=discoveryengine.SearchRequest.SpellCorrectionSpec(
                    mode=discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.AUTO
                ),
            )

            search_response = client.search(request=request)
            summary_text = getattr(search_response.summary, "summary_text", "") if hasattr(search_response, "summary") else ""

            # ========== 2. Prompt ==========
            prompt = (
                "You are a helpful voice assistant. Respond naturally and helpfully. Avoid emojis.\n\n"
                f"--- Context ---\n{summary_text}\n--- END CONTEXT ---\n\n"
                f"User question: {content}"
            )
            # ========== 3. Gemini generation ==========
            model = GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                system_instruction="You are a helpful voice assistant. Respond naturally and helpfully to user queries. Keep responses conversational and engaging. Do not use ANY emojis in your responses."
            )
            chat = model.start_chat(history=[
                {"role": "user", "parts": [content]}
            ])
            response = chat.send_message(prompt, stream=True)

            # ========== 4. Audio streaming synthesis + output ==========
            sentence_buffer = ""
            full_response_text = ""
            sentence_delimiters = re.compile(r'(?<=[.!])\s*')


            for chunk in response:
                if not chunk.text:
                    continue
                yield {"type": "text", "data": chunk.text, "partial": True}
                sentence_buffer += chunk.text
                full_response_text += chunk.text

                sentences = sentence_delimiters.split(sentence_buffer)
                if len(sentences) > 1:
                    for sentence in sentences[:-1]:
                        if sentence.strip():
                            audio = safe_synthesize_speech(sentence.strip())
                            if audio:
                                yield {
                                    "type": "audio",
                                    "session_id": session_data["session_id"],
                                    "mime_type": "audio/wav",
                                    "data": base64.b64encode(audio).decode("utf-8")
                                }
                    sentence_buffer = sentences[-1]

            if sentence_buffer.strip():
                final_audio = safe_synthesize_speech(sentence_buffer.strip())
                if final_audio:
                    yield {
                        "type": "audio",
                        "session_id": session_data["session_id"],
                        "mime_type": "audio/wav",
                        "data": base64.b64encode(final_audio).decode("utf-8")
                    }

            yield {"type": "text", "data": "", "partial": False}

            # ========== 5. Save session ==========
            history = session_data.get("conversation_history", [])
            history.append({"role": "user", "content": content})
            history.append({"role": "model", "content": full_response_text})
            await self.update_session(session_data["session_id"], {"conversation_history": history})

        except Exception as e:
            print(f"❌ Error in _process_text_with_gemini: {e}")
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

import os
import json
import base64
import asyncio
import redis.asyncio as redis
from typing import Dict, Optional, AsyncGenerator, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv

from google.genai.types import (
    Part,
    Content,
    Blob,
)

from google.adk.runners import InMemoryRunner
from google.adk.agents import LiveRequestQueue, Agent
from google.adk.agents.run_config import RunConfig
from google.adk.tools import google_search

from app.config import settings

# Load environment variables
load_dotenv()

APP_NAME = "Voice Assistant"
SESSION_EXPIRY = 3600  # 1 hour


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
        
        # Store ADK sessions and runners
        self.adk_sessions: Dict[str, tuple[AsyncGenerator, LiveRequestQueue]] = {}
        self.adk_runners: Dict[str, InMemoryRunner] = {}
        self.adk_event_tasks: Dict[str, asyncio.Task] = {}  # Background tasks for event processing
        
        # Create the agent for voice interactions
        self.agent = Agent(
            name="voice_assistant",
            model=settings.VOICE_MODEL,
            description="Voice assistant for chat interactions with Google search capability",
            instruction="You are a helpful voice assistant. Respond naturally and helpfully to user queries. When users ask questions that would benefit from current information, use Google search to provide accurate and up-to-date answers. Keep responses conversational and engaging. Format your responses appropriately for voice output.",
            tools=[google_search],
        )
    
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
            
            # Create ADK session for voice processing
            if is_audio:
                await self._create_adk_session(session_id, user_id, is_audio)
            
            print(f"✅ Created voice session: {session_id} for user: {user_id}")
            return session_data
            
        except Exception as e:
            print(f"❌ Error creating Redis voice session: {e}")
            raise
    
    async def _create_adk_session(self, session_id: str, user_id: str, is_audio: bool = True):
        """Create an ADK session for voice processing."""
        try:
            # Create ADK Runner
            runner = InMemoryRunner(
                app_name="Voice Assistant",
                agent=self.agent,
            )
            
            # Create ADK Session
            adk_session = await runner.session_service.create_session(
                app_name="Voice Assistant",
                user_id=user_id,
            )
            
            # Set response modality
            modality = "AUDIO" if is_audio else "TEXT"
            run_config = RunConfig(response_modalities=[modality])
            
            # Create LiveRequestQueue
            live_request_queue = LiveRequestQueue()
            
            # Start agent session
            live_events = runner.run_live(
                session=adk_session,
                live_request_queue=live_request_queue,
                run_config=run_config,
            )
            
            # Store ADK session references
            self.adk_sessions[session_id] = (live_events, live_request_queue)
            self.adk_runners[session_id] = runner
            
            print(f"✅ Created ADK session for: {session_id}")
            
        except Exception as e:
            print(f"❌ Error creating ADK session: {e}")
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
                
                # Use ADK for audio processing
                if session_id in self.adk_sessions:
                    print(f"🔍 Found ADK session for {session_id}")
                    live_events, live_request_queue = self.adk_sessions[session_id]
                    
                    # Send audio data to ADK
                    decoded_data = base64.b64decode(content)
                    print(f"📤 Sending {len(decoded_data)} bytes to ADK")
                    live_request_queue.send_realtime(Blob(data=decoded_data, mime_type=mime_type))
                    
                    # For audio, we don't process events here - they should be handled by SSE
                    # Just acknowledge that we received and sent the audio
                    yield {
                        "type": "status",
                        "message": "Audio data sent to ADK",
                        "bytes_sent": len(decoded_data)
                    }
                else:
                    print(f"❌ No ADK session found for {session_id}. Available: {list(self.adk_sessions.keys())}")
                    yield {"type": "error", "message": "ADK session not found for audio processing"}
                    
            elif mime_type == "text/plain":
                print(f"[REDIS VOICE] Text message: {content}")
                
                # For text messages, use either ADK or direct Gemini
                if session_id in self.adk_sessions and session_data.get("is_audio", False):
                    # Use ADK if audio session exists
                    live_events, live_request_queue = self.adk_sessions[session_id]
                    content_obj = Content(role="user", parts=[Part.from_text(text=content)])
                    live_request_queue.send_content(content=content_obj)
                    
                    async for event in self._process_adk_events(live_events):
                        yield event
                else:
                    # Use direct Gemini for text-only sessions
                    async for event in self._process_text_with_gemini(session_data, content):
                        yield event
            
        except Exception as e:
            print(f"❌ Error in Redis voice processing: {e}")
            yield {"type": "error", "message": str(e)}
    
    async def _process_adk_events(self, live_events: AsyncGenerator) -> AsyncGenerator[Dict[str, Any], None]:
        """Process events from ADK and format them for the client."""
        try:
            async for event in live_events:
                print(f"🔍 Raw ADK event: turn_complete={getattr(event, 'turn_complete', None)}, interrupted={getattr(event, 'interrupted', None)}")
                
                # Handle turn completion and interruption
                if hasattr(event, 'turn_complete') and (event.turn_complete or event.interrupted):
                    print(f"🔚 Control event: turn_complete={event.turn_complete}, interrupted={event.interrupted}")
                    yield {
                        "type": "control",
                        "turn_complete": event.turn_complete,
                        "interrupted": event.interrupted,
                    }
                    continue
                
                # Read the Content and its first Part
                if hasattr(event, 'content') and event.content:
                    print(f"📝 Event has content with {len(event.content.parts) if event.content.parts else 0} parts")
                    part: Part = (
                        event.content and event.content.parts and event.content.parts[0]
                    )
                    if not part:
                        print("⚠️ No part found in event content")
                        continue
                    
                    # Handle audio content
                    is_audio = part.inline_data and part.inline_data.mime_type.startswith("audio/pcm")
                    if is_audio:
                        audio_data = part.inline_data and part.inline_data.data
                        if audio_data:
                            print(f"🔊 Yielding audio response: {len(audio_data)} bytes")
                            yield {
                                "type": "audio",
                                "mime_type": "audio/pcm",
                                "data": base64.b64encode(audio_data).decode("ascii")
                            }
                            continue
                    
                    # Handle text content
                    if part.text:
                        print(f"📄 Text content: '{part.text[:50]}...' (partial={getattr(event, 'partial', False)})")
                        yield {
                            "type": "text",
                            "data": part.text,
                            "partial": getattr(event, 'partial', False)
                        }
                else:
                    print(f"⚠️ Event has no content: {type(event).__name__}")
        except Exception as e:
            print(f"❌ Error processing ADK events: {e}")
            import traceback
            traceback.print_exc()
    
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
    

    
    async def _process_single_adk_event(self, event) -> Optional[Dict[str, Any]]:
        """Process a single ADK event and return formatted result."""
        try:
            print(f"🔍 Processing ADK event: {type(event).__name__}")
            
            # Handle turn completion and interruption
            if hasattr(event, 'turn_complete') and (event.turn_complete or event.interrupted):
                print(f"🔚 Control event: turn_complete={event.turn_complete}, interrupted={event.interrupted}")
                return {
                    "type": "control",
                    "turn_complete": event.turn_complete,
                    "interrupted": event.interrupted,
                }
            
            # Read the Content and its first Part
            if hasattr(event, 'content') and event.content:
                print(f"📝 Event has content with {len(event.content.parts) if event.content.parts else 0} parts")
                part: Part = (
                    event.content and event.content.parts and event.content.parts[0]
                )
                if not part:
                    print("⚠️ No part found in event content")
                    return None
                
                # Handle audio content
                is_audio = part.inline_data and part.inline_data.mime_type.startswith("audio/pcm")
                if is_audio:
                    audio_data = part.inline_data and part.inline_data.data
                    if audio_data:
                        print(f"🔊 Audio response: {len(audio_data)} bytes")
                        return {
                            "type": "audio",
                            "mime_type": "audio/pcm",
                            "data": base64.b64encode(audio_data).decode("ascii")
                        }
                
                # Handle text content
                if part.text:
                    print(f"📄 Text content: '{part.text[:50]}...' (partial={getattr(event, 'partial', False)})")
                    return {
                        "type": "text",
                        "data": part.text,
                        "partial": getattr(event, 'partial', False)
                    }
            else:
                print(f"⚠️ Event has no content: {type(event).__name__}")
                
        except Exception as e:
            print(f"❌ Error processing single ADK event: {e}")
            return {"type": "error", "message": f"Event processing error: {str(e)}"}
        
        return None
    

    
    async def close_session(self, session_id: str) -> bool:
        """
        Close a voice session and clean up ADK resources.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful
        """
        try:
            # Close ADK session if exists
            if session_id in self.adk_sessions:
                live_events, live_request_queue = self.adk_sessions[session_id]
                live_request_queue.close()
                del self.adk_sessions[session_id]
            
            # Clean up ADK runner
            if session_id in self.adk_runners:
                del self.adk_runners[session_id]
            
            # Remove from Redis
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
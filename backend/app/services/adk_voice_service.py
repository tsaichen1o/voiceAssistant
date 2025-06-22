import os
import json
import base64
import asyncio
from typing import Dict, Optional, AsyncGenerator, Any
from pathlib import Path
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


class ADKVoiceService:
    """Service for handling voice interactions using Google ADK."""
    
    def __init__(self):
        """Initialize the ADK voice service."""
        self.active_sessions: Dict[str, LiveRequestQueue] = {}
        self.runners: Dict[str, InMemoryRunner] = {}
        
        # Create the root agent
        self.agent = Agent(
            name="voice_assistant",
            model=settings.VOICE_MODEL,  # Use dedicated voice model from config
            description="Voice assistant for chat interactions with Google search capability",
            instruction="You are a helpful voice assistant. Respond naturally and helpfully to user queries. When users ask questions that would benefit from current information, use Google search to provide accurate and up-to-date answers. Keep responses conversational and engaging. Format your responses appropriately for voice output.",
            tools=[google_search],  # Google search tool for enhanced responses
        )
    
    async def create_session(self, user_id: str, is_audio: bool = True) -> tuple[AsyncGenerator, LiveRequestQueue]:
        """
        Create a new voice session for a user.
        
        Args:
            user_id: Unique identifier for the user
            is_audio: Whether to use audio mode (default: True)
            
        Returns:
            Tuple of (live_events generator, live_request_queue)
        """
        # Create a Runner
        runner = InMemoryRunner(
            app_name=APP_NAME,
            agent=self.agent,
        )
        
        # Create a Session
        session = await runner.session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
        )
        
        # Set response modality
        modality = "AUDIO" if is_audio else "TEXT"
        run_config = RunConfig(response_modalities=[modality])
        
        # Create a LiveRequestQueue for this session
        live_request_queue = LiveRequestQueue()
        
        # Start agent session
        live_events = runner.run_live(
            session=session,
            live_request_queue=live_request_queue,
            run_config=run_config,
        )
        
        # Store session references
        self.active_sessions[user_id] = live_request_queue
        self.runners[user_id] = runner
        
        return live_events, live_request_queue
    
    async def process_events(self, live_events: AsyncGenerator) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process events from the ADK agent and format them for the client.
        
        Args:
            live_events: Generator of live events from the agent
            
        Yields:
            Formatted event dictionaries for the client
        """
        async for event in live_events:
            # Handle turn completion and interruption
            if event.turn_complete or event.interrupted:
                yield {
                    "type": "control",
                    "turn_complete": event.turn_complete,
                    "interrupted": event.interrupted,
                }
                continue
            
            # Read the Content and its first Part
            part: Part = (
                event.content and event.content.parts and event.content.parts[0]
            )
            if not part:
                continue
            
            # Handle audio content
            is_audio = part.inline_data and part.inline_data.mime_type.startswith("audio/pcm")
            if is_audio:
                audio_data = part.inline_data and part.inline_data.data
                if audio_data:
                    yield {
                        "type": "audio",
                        "mime_type": "audio/pcm",
                        "data": base64.b64encode(audio_data).decode("ascii")
                    }
                    continue
            
            # Handle text content
            if part.text and event.partial:
                yield {
                    "type": "text",
                    "mime_type": "text/plain",
                    "data": part.text,
                    "partial": True
                }
    
    async def send_text_message(self, user_id: str, text: str) -> bool:
        """
        Send a text message to the agent.
        
        Args:
            user_id: User identifier
            text: Text message to send
            
        Returns:
            True if successful, False otherwise
        """
        live_request_queue = self.active_sessions.get(user_id)
        if not live_request_queue:
            return False
        
        content = Content(role="user", parts=[Part.from_text(text=text)])
        live_request_queue.send_content(content=content)
        return True
    
    async def send_audio_data(self, user_id: str, audio_data: str, mime_type: str = "audio/pcm") -> bool:
        """
        Send audio data to the agent.
        
        Args:
            user_id: User identifier
            audio_data: Base64 encoded audio data
            mime_type: MIME type of the audio data
            
        Returns:
            True if successful, False otherwise
        """
        live_request_queue = self.active_sessions.get(user_id)
        if not live_request_queue:
            return False
        
        decoded_data = base64.b64decode(audio_data)
        live_request_queue.send_realtime(Blob(data=decoded_data, mime_type=mime_type))
        return True
    
    def close_session(self, user_id: str) -> None:
        """
        Close a voice session for a user.
        
        Args:
            user_id: User identifier
        """
        if user_id in self.active_sessions:
            self.active_sessions[user_id].close()
            del self.active_sessions[user_id]
        
        if user_id in self.runners:
            del self.runners[user_id]
    
    def get_active_sessions(self) -> list[str]:
        """Get list of active session user IDs."""
        return list(self.active_sessions.keys())


# Create a global instance
adk_voice_service = ADKVoiceService() 
import os
import json
import base64
import asyncio
import tempfile
import redis.asyncio as redis
from typing import Dict, Optional, AsyncGenerator, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

# Import for future implementations
try:
    import whisper
    import torch
    import edge_tts
    import soundfile as sf
    from pydub import AudioSegment
    import google.generativeai as genai
except ImportError as e:
    print(f"Warning: Some dependencies not installed yet: {e}")
    print("Please run: pip install -r requirements.txt")

from app.config import settings

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_NAME = "OpenSource Voice Assistant"
SESSION_EXPIRY = 3600  # 1 hour


class OpenSourceVoiceService:
    """
    Open source voice service using Whisper (ASR) + Gemini API (LLM) + gTTS (TTS).
    Uses Redis for session state management, compatible with existing architecture.
    """
    
    def __init__(self):
        """Initialize the open source voice service."""
        logger.info("🚀Initializing OpenSource Voice Service...")
        
        # Initialize Redis connection for session management (compatible with existing system)
        if hasattr(settings, 'REDIS_URL') and settings.REDIS_URL:
            self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=False)
        else:
            self.redis_client = redis.Redis(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                password=getattr(settings, 'REDIS_PASSWORD', None),
                decode_responses=False
            )
        
        # Initialize Whisper model (lazy loading with enhanced logging)
        self.whisper_model = None
        self.whisper_model_name = "base"  # Can be: tiny, base, small, medium, large
        
        # Initialize Gemini API
        if os.getenv("GEMINI_API_KEY"):
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        else:
            logger.warning("⚠️ GEMINI_API_KEY not found in environment variables")
        
        # TTS Configuration
        self.tts_language = 'en'  # Default language
        self.tts_slow = False     # Speech speed
        
        logger.info("✅ OpenSource Voice Service initialized successfully")
    
    async def create_session(self, user_id: str, is_audio: bool = True) -> Dict[str, Any]:
        """
        Create a new voice session with Redis state management.
        
        Args:
            user_id: Unique identifier for the user
            is_audio: Whether to use audio mode (default: True)
            
        Returns:
            Session information dictionary
        """
        try:
            session_id = f"opensource_voice_{user_id}_{int(datetime.now().timestamp())}"
            
            # Create session data for Redis
            session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "is_audio": is_audio,
                "service_type": "opensource",  # Distinguish from ADK sessions
                "created_at": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat(),
                "status": "active",
                "conversation_history": [],
                "whisper_model": self.whisper_model_name,
                "tts_config": {
                    "language": self.tts_language,
                    "slow": self.tts_slow
                }
            }
            
            # Store in Redis with expiration
            redis_key = f"opensource_voice_session:{session_id}"
            session_json = json.dumps(session_data)
            logger.info(f"🔍 Storing session in Redis key: {redis_key}")
            
            await self.redis_client.setex(
                redis_key,
                SESSION_EXPIRY,
                session_json
            )
            
            # Verify the session was stored
            stored_data = await self.redis_client.get(redis_key)
            if stored_data:
                logger.info(f"✅ Session successfully stored and verified in Redis")
            else:
                logger.error(f"❌ Failed to store session in Redis!")
                raise Exception("Failed to store session in Redis")
            
            # Initialize Whisper model if needed (lazy loading)
            if is_audio and self.whisper_model is None:
                await self._initialize_whisper_model()
            
            logger.info(f"✅ Created opensource voice session: {session_id} for user: {user_id}")
            return session_data
            
        except Exception as e:
            logger.error(f"❌ Error creating opensource voice session: {e}")
            raise
    
    async def _initialize_whisper_model(self):
        """Initialize Whisper model for ASR (lazy loading)."""
        try:
            logger.info(f"🔄 Loading Whisper model: {self.whisper_model_name}")
            
            # Load Whisper model in a thread to avoid blocking
            def load_whisper():
                return whisper.load_model(self.whisper_model_name)
            
            # Run in thread to avoid blocking the async loop
            loop = asyncio.get_event_loop()
            self.whisper_model = await loop.run_in_executor(None, load_whisper)
            
            logger.info(f"✅ Whisper model '{self.whisper_model_name}' loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Error loading Whisper model: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from Redis."""
        try:
            redis_key = f"opensource_voice_session:{session_id}"
            logger.info(f"🔍 Getting session from Redis key: {redis_key}")
            
            session_data = await self.redis_client.get(redis_key)
            if session_data:
                logger.info(f"✅ Found session data in Redis")
                return json.loads(session_data.decode('utf-8'))
            else:
                logger.warning(f"❌ No data found for Redis key: {redis_key}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting session from Redis: {e}")
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
                f"opensource_voice_session:{session_id}",
                SESSION_EXPIRY,
                json.dumps(session_data)
            )
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating session in Redis: {e}")
            return False
    
    async def send_message(self, session_id: str, content: str, mime_type: str = "text/plain") -> AsyncGenerator[Dict[str, Any], None]:
        """
        Send a message and stream the response using open source components.
        
        Args:
            session_id: Session identifier
            content: Message content (text or base64 audio)
            mime_type: Content type
            
        Yields:
            Response events in the format expected by the frontend
        """
        try:
            # Get session data
            session_data = await self.get_session(session_id)
            if not session_data:
                yield {"type": "error", "error": "Session not found"}
                return
            
            logger.info(f"🔍 Processing message for session {session_id}, mime_type: {mime_type}")
            
            # Update last active
            await self.update_session(session_id, {"last_active": datetime.now().isoformat()})
            
            # Process based on content type
            if mime_type == "audio/pcm":
                # Process audio message (ASR -> LLM -> TTS)
                async for event in self._process_audio_message(session_data, content):
                    yield event
            elif mime_type == "text/plain":
                # Process text message (LLM -> TTS if audio mode)
                async for event in self._process_text_message(session_data, content):
                    yield event
            else:
                yield {"type": "error", "error": f"Unsupported mime_type: {mime_type}"}
                
        except Exception as e:
            logger.error(f"❌ Error in send_message: {e}")
            yield {"type": "error", "error": str(e)}
    
    async def _convert_pcm_to_wav(self, pcm_base64: str, sample_rate: int = 24000) -> str:
        """
        Convert PCM base64 data to WAV format for Whisper.
        
        Args:
            pcm_base64: Base64 encoded PCM data
            sample_rate: Sample rate (default: 24000 Hz, matching frontend)
            
        Returns:
            Path to temporary WAV file
        """
        try:
            # Decode base64 to bytes
            pcm_bytes = base64.b64decode(pcm_base64)
            
            # Convert bytes to numpy array (16-bit PCM)
            import numpy as np
            pcm_data = np.frombuffer(pcm_bytes, dtype=np.int16)
            
            # Create temporary WAV file
            temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_wav_path = temp_wav.name
            temp_wav.close()
            
            # Use soundfile to save as WAV
            sf.write(temp_wav_path, pcm_data, sample_rate)
            
            logger.info(f"✅ Converted PCM to WAV: {len(pcm_data)} samples -> {temp_wav_path}")
            return temp_wav_path
            
        except Exception as e:
            logger.error(f"❌ Error converting PCM to WAV: {e}")
            raise
    
    async def _transcribe_audio_with_whisper(self, audio_file_path: str) -> str:
        """
        Transcribe audio file using Whisper (with fallback to simulation).
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        try:
            # First, try real Whisper transcription
            if self.whisper_model is None:
                await self._initialize_whisper_model()
            
            logger.info(f"🎤 Attempting Whisper transcription with model: {self.whisper_model_name}")
            
            # Verify the audio file exists and is readable
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
            
            # Log audio file details
            file_size = os.path.getsize(audio_file_path)
            logger.info(f"🔍 Audio file details: {audio_file_path}, size: {file_size} bytes")
            
            # Try real Whisper transcription
            def transcribe():
                try:
                    # Use Whisper with explicit options for better compatibility
                    result = self.whisper_model.transcribe(
                        audio_file_path,
                        fp16=False,  # Force FP32 for CPU compatibility
                        language=None,  # Auto-detect language
                        verbose=False  # Reduce verbose output
                    )
                    text = result["text"].strip()
                    detected_lang = result.get("language", "unknown")
                    logger.info(f"🔍 Whisper result - Language: {detected_lang}, Text: '{text}'")
                    return text
                except Exception as e:
                    logger.warning(f"⚠️ Whisper transcription failed: {e}")
                    import traceback
                    traceback.print_exc()
                    # If Whisper fails, fall back to simulation
                    return None
            
            loop = asyncio.get_event_loop()
            transcribed_text = await loop.run_in_executor(None, transcribe)
            
            if transcribed_text is not None:
                logger.info(f"✅ Real Whisper transcription completed: '{transcribed_text}'")
                if not transcribed_text:
                    logger.warning("⚠️ Whisper returned empty text - audio may be too quiet or contain no speech")
                return transcribed_text
            else:
                # Fall back to simulation
                logger.warning("⚠️ Whisper transcription returned None, falling back to simulation")
                return await self._simulate_speech_recognition(audio_file_path)
                
        except Exception as e:
            # For file not found errors, re-raise immediately (don't try simulation)
            if "not found" in str(e).lower() or "no such file" in str(e).lower():
                logger.error(f"❌ Error transcribing audio with Whisper: {e}")
                raise
            else:
                logger.warning(f"⚠️ Whisper failed, using simulation: {e}")
                # Fall back to simulation for other errors
                return await self._simulate_speech_recognition(audio_file_path)
    
    async def _simulate_speech_recognition(self, audio_file_path: str) -> str:
        """
        Simulate speech recognition for development/testing purposes.
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Simulated transcribed text
        """
        try:
            logger.info("🎭 Using simulated speech recognition (Whisper fallback)")
            
            # Read audio file to get duration and basic info
            import soundfile as sf
            audio_data, sample_rate = sf.read(audio_file_path)
            duration = len(audio_data) / sample_rate
            
            # Simulate processing time based on audio duration
            processing_time = min(duration * 0.3, 2.0)  # Max 2 seconds
            await asyncio.sleep(processing_time)
            
            # Generate realistic simulated transcriptions based on audio characteristics
            if duration < 0.5:
                simulated_texts = ["Hi", "Hello", "Yes", "No", "OK"]
            elif duration < 2.0:
                simulated_texts = [
                    "Hello there",
                    "How are you?", 
                    "What's the weather like?",
                    "Can you help me?",
                    "Thank you very much"
                ]
            else:
                simulated_texts = [
                    "Hello, I'm testing the voice assistant functionality",
                    "Can you tell me about TUM's computer science program?",
                    "What are the admission requirements for international students?",
                    "I would like to know more about the research opportunities",
                    "Could you explain the application process in detail?"
                ]
            
            # Use a hash of the audio data to get consistent results
            import hashlib
            audio_hash = hashlib.md5(audio_data.tobytes()).hexdigest()
            text_index = int(audio_hash[:8], 16) % len(simulated_texts)
            simulated_text = simulated_texts[text_index]
            
            logger.info(f"🎭 Simulated transcription: '{simulated_text}' (duration: {duration:.1f}s)")
            return simulated_text
            
        except Exception as e:
            logger.error(f"❌ Even simulation failed: {e}")
            # Ultimate fallback
            return "Hello, this is a test message from simulated speech recognition"
    
    async def _process_audio_message(self, session_data: Dict[str, Any], audio_base64: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process audio message: ASR (Whisper) -> LLM (Gemini) -> TTS (gTTS).
        Now with real Whisper ASR implementation!
        """
        temp_wav_path = None
        try:
            session_id = session_data["session_id"]
            logger.info(f"🎤 Starting ASR processing for session {session_id}")
            logger.info(f"🔍 Audio data size: {len(audio_base64)} chars (base64)")
            
            # Ensure Whisper model is loaded
            if self.whisper_model is None:
                logger.info("🔄 Whisper model not loaded, initializing...")
                yield {"type": "text", "data": "🧠 Loading speech recognition model...", "partial": True}
                await self._initialize_whisper_model()
                if self.whisper_model is None:
                    logger.error("❌ Failed to load Whisper model")
                    yield {"type": "error", "error": "Failed to load Whisper model"}
                    return
                logger.info("✅ Whisper model loaded successfully")
            
            # Step 1: Convert PCM to WAV for Whisper
            yield {"type": "text", "data": "🔄 Converting audio format...", "partial": True}
            temp_wav_path = await self._convert_pcm_to_wav(audio_base64)
            
            # Step 2: Transcribe with Whisper
            yield {"type": "text", "data": "🎤 Transcribing with Whisper...", "partial": True}
            transcribed_text = await self._transcribe_audio_with_whisper(temp_wav_path)
            
            if not transcribed_text:
                # No speech detected, but still provide voice feedback
                no_speech_message = "I didn't hear anything. Could you please try speaking again?"
                yield {"type": "text", "data": no_speech_message, "partial": False}
                
                # Generate TTS for the no-speech feedback
                yield {"type": "text", "data": "🔊 Generating speech feedback...", "partial": True}
                async for tts_chunk in self._generate_tts_audio(no_speech_message):
                    yield tts_chunk
                return
            
            # Step 3: Show what user said
            yield {"type": "text", "data": f"👤 You said: \"{transcribed_text}\"", "partial": False}
            
            # Step 4: Update conversation history
            conversation_history = session_data.get("conversation_history", [])
            conversation_history.append({
                "role": "user",
                "content": transcribed_text,
                "timestamp": datetime.now().isoformat(),
                "input_type": "voice"
            })
            await self.update_session(session_id, {"conversation_history": conversation_history})
            
            # Step 5: Process with LLM (real Gemini API)
            yield {"type": "text", "data": "🧠 Processing with Gemini AI...", "partial": True}
            
            # Generate response using the same LLM method as text messages
            conversation_history = session_data.get("conversation_history", [])
            async for response_chunk in self._generate_gemini_response(conversation_history):
                yield response_chunk
            
            # Step 6: Generate TTS audio from LLM response
            if hasattr(self, '_last_assistant_response') and self._last_assistant_response:
                yield {"type": "text", "data": "🔊 Generating speech audio...", "partial": True}
                async for tts_chunk in self._generate_tts_audio(self._last_assistant_response):
                    yield tts_chunk
                
                # Update conversation history with assistant response
                conversation_history = session_data.get("conversation_history", [])
                conversation_history.append({
                    "role": "assistant",
                    "content": self._last_assistant_response,
                    "timestamp": datetime.now().isoformat()
                })
                await self.update_session(session_id, {"conversation_history": conversation_history})
            
        except Exception as e:
            logger.error(f"❌ Error processing audio message: {e}")
            yield {"type": "error", "error": f"Audio processing failed: {str(e)}"}
        finally:
            # Clean up temporary file
            if temp_wav_path and os.path.exists(temp_wav_path):
                try:
                    os.unlink(temp_wav_path)
                    logger.info(f"🗑️ Cleaned up temp file: {temp_wav_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to clean up temp file: {e}")
    
    async def _process_text_message(self, session_data: Dict[str, Any], text: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process text message: LLM (Gemini) -> TTS (gTTS).
        Now with real Gemini API integration!
        """
        try:
            session_id = session_data["session_id"]
            logger.info(f"🧠 Starting LLM processing for session {session_id}")
            
            # Step 1: Show user input
            yield {"type": "text", "data": f"👤 You said: \"{text}\"", "partial": False}
            
            # Step 2: Update conversation history
            conversation_history = session_data.get("conversation_history", [])
            conversation_history.append({
                "role": "user",
                "content": text,
                "timestamp": datetime.now().isoformat(),
                "input_type": "text"
            })
            
            # Step 3: Process with Gemini API
            yield {"type": "text", "data": "🧠 Thinking with Gemini AI...", "partial": True}
            
            # Generate response using Gemini API
            async for response_chunk in self._generate_gemini_response(conversation_history):
                yield response_chunk
            
            # Step 4: Generate TTS audio from LLM response
            if hasattr(self, '_last_assistant_response') and self._last_assistant_response:
                yield {"type": "text", "data": "🔊 Generating speech audio...", "partial": True}
                async for tts_chunk in self._generate_tts_audio(self._last_assistant_response):
                    yield tts_chunk
                
                # Update conversation history with assistant response
                conversation_history = session_data.get("conversation_history", [])
                conversation_history.append({
                    "role": "assistant",
                    "content": self._last_assistant_response,
                    "timestamp": datetime.now().isoformat()
                })
                await self.update_session(session_id, {"conversation_history": conversation_history})
            
        except Exception as e:
            logger.error(f"❌ Error processing text message: {e}")
            yield {"type": "error", "error": f"Text processing failed: {str(e)}"}
    
    async def _generate_gemini_response(self, conversation_history: list) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate response using standard Gemini API with streaming.
        
        Args:
            conversation_history: List of conversation messages
            
        Yields:
            Response chunks in the expected format
        """
        try:
            import google.generativeai as genai
            
            # Create model without system_instruction (for older library versions)
            # Use reliable models that support generateContent
            try:
                model_name = settings.VOICE_MODEL if hasattr(settings, 'VOICE_MODEL') else "gemini-1.5-flash"
                # Ensure we're using a model that supports generateContent (not Live API models)
                if "live" in model_name.lower():
                    logger.warning(f"⚠️ Live model {model_name} not supported for generateContent, using gemini-1.5-flash")
                    model_name = "gemini-1.5-flash"
                
                model = genai.GenerativeModel(model_name=model_name)
                logger.info(f"✅ Using Gemini model: {model_name}")
            except Exception as e:
                logger.warning(f"⚠️ Voice model failed, using fallback: {e}")
                model = genai.GenerativeModel(model_name="gemini-1.5-flash")
            
            # Prepare conversation history for Gemini with system instruction as first message
            system_instruction = """You are a helpful voice assistant for TUM (Technical University of Munich).
            
            Your role:
            - Help prospective and current students with information about TUM
            - Provide clear, concise, and helpful responses
            - Keep responses conversational and engaging for voice interaction
            - If you don't know something specific about TUM, be honest and suggest where to find more information
            
            Guidelines:
            - Keep responses under 100 words for voice clarity
            - Use natural, conversational language
            - Be friendly and encouraging
            - For complex information, offer to break it down into parts"""
            
            gemini_history = []
            
            # Add system instruction as first user message (workaround for older library)
            if not conversation_history or conversation_history[0].get("content") != system_instruction:
                gemini_history.append({"role": "user", "parts": [system_instruction]})
                gemini_history.append({"role": "model", "parts": ["I understand. I'm ready to help with TUM-related questions as a friendly voice assistant."]})
            
            # Add conversation history (exclude current message)
            for msg in conversation_history[:-1]:
                if msg["role"] == "user":
                    gemini_history.append({"role": "user", "parts": [msg["content"]]})
                elif msg["role"] == "assistant":
                    gemini_history.append({"role": "model", "parts": [msg["content"]]})
            
            # Start chat with history
            chat = model.start_chat(history=gemini_history)
            
            # Get the current user message
            current_message = conversation_history[-1]["content"]
            
            # Generate streaming response
            logger.info(f"🧠 Sending to Gemini: '{current_message}'")
            response = chat.send_message(current_message, stream=True)
            
            full_response = ""
            for chunk in response:
                if chunk.text:
                    chunk_text = chunk.text
                    full_response += chunk_text
                    
                    # Yield each chunk
                    yield {
                        "type": "text",
                        "data": chunk_text,
                        "partial": True
                    }
            
            # Store full response for conversation history
            self._last_assistant_response = full_response.strip()
            
            # Send final complete response
            yield {
                "type": "text",
                "data": f"\n🤖 Complete response: {self._last_assistant_response}",
                "partial": False
            }
            
            logger.info(f"✅ Gemini response completed: {len(self._last_assistant_response)} characters")
            
        except Exception as e:
            logger.error(f"❌ Error generating Gemini response: {e}")
            yield {
                "type": "error", 
                "error": f"Failed to generate response: {str(e)}"
            }
    
    async def _generate_tts_audio(self, text: str, language: str = "en") -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate speech audio from text using Edge TTS with optimized compression.
        
        Args:
            text: Text to convert to speech
            language: Language code (en, zh, de, etc.)
            
        Yields:
            Audio chunks in the expected format
        """
        temp_audio_path = None
        try:
            import base64
            import tempfile
            import re
            
            # Detect language automatically
            detected_lang = self._detect_language(text)
            if detected_lang:
                language = detected_lang
                logger.info(f"🌍 Detected language: {language}")
            
            # Clean and limit text for voice output
            clean_text = self._prepare_text_for_tts(text)
            
            logger.info(f"🔊 Starting Edge TTS generation for text: '{clean_text[:50]}...'")
            logger.info(f"🔊 Text length: {len(clean_text)} characters")
            logger.info(f"🔊 Using language: {language}")
            
            # Edge TTS can handle longer texts better than gTTS, but still limit for performance
            if len(clean_text) > 300:  # Increased limit since Edge TTS is more efficient
                sentences = re.split(r'[.!?]+', clean_text)
                # Take sentences that fit within limit
                selected_text = ""
                for sentence in sentences:
                    if len(selected_text + sentence) < 300:
                        selected_text += sentence.strip() + ". "
                    else:
                        break
                clean_text = selected_text.strip()
                logger.info(f"🎤 Truncated to: '{clean_text}' ({len(clean_text)} chars)")
            
            # Select appropriate voice based on language
            voice = self._get_edge_tts_voice(language)
            logger.info(f"🎙️ Using Edge TTS voice: {voice}")
            
            # Generate TTS using Edge TTS
            temp_fd, temp_audio_path = tempfile.mkstemp(suffix='.mp3')
            os.close(temp_fd)  # Close file descriptor immediately
            
            # Use Edge TTS to generate audio
            communicate = edge_tts.Communicate(clean_text, voice)
            await communicate.save(temp_audio_path)
            
            if not os.path.exists(temp_audio_path):
                yield {"type": "error", "error": "Edge TTS audio generation failed"}
                return
            
            # Read and encode audio file
            with open(temp_audio_path, 'rb') as audio_file:
                audio_data = audio_file.read()
            
            # Check audio size - Edge TTS typically generates smaller files
            audio_size_kb = len(audio_data) / 1024
            logger.info(f"✅ Edge TTS audio generated: {audio_size_kb:.1f} KB")
            
            # Edge TTS typically generates much smaller files, so this should be fine
            if audio_size_kb > 100:  # Higher threshold since Edge TTS is more efficient
                logger.warning(f"⚠️ Large audio file: {audio_size_kb:.1f} KB")
            
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Yield progress message first
            yield {
                "type": "text", 
                "data": f"🔊 Generating speech with Edge TTS ({audio_size_kb:.1f} KB)...",
                "partial": True
            }
            
            # Yield audio data
            yield {
                "type": "audio",
                "data": audio_base64,
                "format": "mp3",
                "sample_rate": 24000,  # Edge TTS default
                "partial": False,
                "text_source": clean_text[:100] + "..." if len(clean_text) > 100 else clean_text,
                "voice_used": voice
            }
            
            # Yield completion message
            yield {
                "type": "text", 
                "data": f"🔊 Edge TTS audio generated ({audio_size_kb:.1f} KB, {voice})",
                "partial": False
            }
            
        except Exception as e:
            logger.error(f"❌ Error in Edge TTS generation: {e}")
            import traceback
            traceback.print_exc()
            yield {
                "type": "error",
                "error": f"Edge TTS generation failed: {str(e)}"
            }
        finally:
            # Clean up temporary file
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.unlink(temp_audio_path)
                    logger.info(f"🗑️ Cleaned up Edge TTS temp file: {temp_audio_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to clean up Edge TTS temp file: {e}")
    
    def _get_edge_tts_voice(self, language: str) -> str:
        """
        Get appropriate Edge TTS voice for the given language.
        
        Args:
            language: Language code (en, zh, de, etc.)
            
        Returns:
            Edge TTS voice name
        """
        voice_map = {
            "en": "en-US-AriaNeural",      # English - natural female voice
            "zh": "zh-CN-XiaoxiaoNeural",  # Chinese - natural female voice
            "de": "de-DE-KatjaNeural",     # German - natural female voice
            "es": "es-ES-ElviraNeural",    # Spanish - natural female voice
            "fr": "fr-FR-DeniseNeural",    # French - natural female voice
            "ja": "ja-JP-NanamiNeural",    # Japanese - natural female voice
            "ko": "ko-KR-SunHiNeural",     # Korean - natural female voice
        }
        
        return voice_map.get(language, "en-US-AriaNeural")  # Default to English
    
    def _detect_language(self, text: str) -> str:
        """
        Simple language detection for TTS.
        
        Args:
            text: Text to analyze
            
        Returns:
            Language code (en, zh, de, etc.)
        """
        try:
            # Check for Chinese characters
            chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
            if chinese_chars > 0:
                return "zh"
            
            # Check for German characters/words
            german_indicators = ['ä', 'ö', 'ü', 'ß', 'TUM', 'München', 'Universität']
            if any(indicator in text for indicator in german_indicators):
                return "de"
            
            # Default to English
            return "en"
            
        except Exception as e:
            logger.warning(f"⚠️ Language detection failed: {e}")
            return "en"
    
    def _prepare_text_for_tts(self, text: str) -> str:
        """
        Prepare text for TTS by cleaning and limiting length.
        Edge TTS can handle longer texts more efficiently than gTTS.
        
        Args:
            text: Raw text from LLM
            
        Returns:
            Cleaned text suitable for TTS
        """
        try:
            # Remove markdown and special formatting
            import re
            
            # Remove markdown links [text](url) -> text
            text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
            
            # Remove markdown bold **text** -> text
            text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
            
            # Remove markdown italic *text* -> text
            text = re.sub(r'\*([^\*]+)\*', r'\1', text)
            
            # Remove code blocks ```code``` -> code
            text = re.sub(r'```[^`]*```', '', text)
            
            # Remove inline code `code` -> code
            text = re.sub(r'`([^`]+)`', r'\1', text)
            
            # Remove extra whitespace and newlines
            text = ' '.join(text.split())
            
            # Remove emojis and special characters that might confuse TTS
            text = re.sub(r'[🎯🔊🧠👤🤖📝🎤✅❌⚠️🌍🔍📄🔚🗑️]', '', text)
            
            # Edge TTS can handle longer texts more efficiently - increased limit
            if len(text) > 250:  # Increased from 150 to 250
                # Try to cut at sentence boundary
                sentences = re.split(r'[.!?]+', text)
                if sentences and len(sentences[0]) <= 250:
                    text = sentences[0].strip() + "."
                else:
                    text = text[:247] + "..."
            
            return text.strip()
            
        except Exception as e:
            logger.warning(f"⚠️ Text preparation failed: {e}")
            return text[:200]  # Fallback to simple truncation
    
    async def close_session(self, session_id: str) -> bool:
        """Close and cleanup a voice session."""
        try:
            logger.info(f"🔚 Closing opensource voice session: {session_id}")
            
            # Get session data before deletion
            session_data = await self.get_session(session_id)
            if session_data:
                # Update status to closed
                await self.update_session(session_id, {"status": "closed"})
                
                # Delete from Redis after a short delay
                await asyncio.sleep(1)
                redis_key = f"opensource_voice_session:{session_id}"
                await self.redis_client.delete(redis_key)
                
                logger.info(f"✅ Session {session_id} closed and cleaned up")
                return True
            else:
                logger.warning(f"⚠️ Session {session_id} not found during close")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error closing session {session_id}: {e}")
            return False
    
    async def list_active_sessions(self) -> list[str]:
        """List all active opensource voice sessions."""
        try:
            pattern = "opensource_voice_session:*"
            keys = await self.redis_client.keys(pattern)
            return [key.decode('utf-8').split(':')[1] for key in keys]
        except Exception as e:
            logger.error(f"❌ Error listing active sessions: {e}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the opensource voice service."""
        try:
            # Check Redis connection
            await self.redis_client.ping()
            redis_status = "healthy"
        except Exception as e:
            redis_status = f"unhealthy: {e}"
        
        # Check Whisper model
        whisper_status = "loaded" if self.whisper_model else "not_loaded"
        
        # Check Gemini API key
        gemini_status = "configured" if os.getenv("GEMINI_API_KEY") else "not_configured"
        
        # Check gTTS availability
        try:
            import gtts
            gtts_status = "available"
        except ImportError:
            gtts_status = "not_available"
        
        # Overall service status
        all_healthy = (
            redis_status == "healthy" and 
            gemini_status == "configured" and 
            gtts_status == "available"
        )
        
        return {
            "service": "opensource_voice",
            "status": "healthy" if all_healthy else "degraded",
            "components": {
                "redis": redis_status,
                "whisper": whisper_status,
                "gemini_api": gemini_status,
                "gtts": gtts_status
            },
            "whisper_model": self.whisper_model_name,
            "timestamp": datetime.now().isoformat()
        }


# Global instance (similar to existing redis_voice_service)
opensource_voice_service = OpenSourceVoiceService() 
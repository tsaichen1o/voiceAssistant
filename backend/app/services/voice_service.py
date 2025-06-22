import base64
import io
import os
from typing import Optional, Dict, Any
from google.cloud import speech
from pydub import AudioSegment
from pydub.effects import normalize
import tempfile

from app.config import settings
from app.models.schemas import VoiceRequest, TranscriptionResponse


class VoiceService:
    """Service for handling voice transcription and audio processing."""
    
    def __init__(self):
        """Initialize the voice service with Google Speech client."""
        # Set up Google Cloud credentials if provided
        if settings.GOOGLE_APPLICATION_CREDENTIALS:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = settings.GOOGLE_APPLICATION_CREDENTIALS
        
        try:
            self.speech_client = speech.SpeechClient()
        except Exception as e:
            print(f"Warning: Could not initialize Google Speech client: {e}")
            self.speech_client = None
    
    async def transcribe_audio(self, voice_request: VoiceRequest) -> TranscriptionResponse:
        """
        Transcribe audio data to text using Google Speech-to-Text API.
        
        Args:
            voice_request: The voice request containing base64 encoded audio data
            
        Returns:
            TranscriptionResponse: The transcription result
            
        Raises:
            ValueError: If the audio data is invalid or cannot be processed
            RuntimeError: If the speech client is not available
        """
        if not self.speech_client:
            raise RuntimeError("Google Speech client is not available. Please check your credentials.")
        
        try:
            # Decode base64 audio data
            audio_data = base64.b64decode(voice_request.audio_data)
            
            # Process audio data
            processed_audio = self._preprocess_audio(audio_data)
            
            # Configure recognition request
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                sample_rate_hertz=48000,  # Common web audio sample rate
                language_code=voice_request.language or settings.SPEECH_LANGUAGE_CODE,
                enable_automatic_punctuation=True,
                enable_word_confidence=True,
                model="latest_long",  # Use the latest model for better accuracy
            )
            
            audio = speech.RecognitionAudio(content=processed_audio)
            
            # Perform the transcription
            response = self.speech_client.recognize(config=config, audio=audio)
            
            if not response.results:
                return TranscriptionResponse(
                    text="",
                    confidence=0.0
                )
            
            # Get the best result
            result = response.results[0]
            alternative = result.alternatives[0]
            
            return TranscriptionResponse(
                text=alternative.transcript,
                confidence=alternative.confidence
            )
            
        except Exception as e:
            print(f"Error during transcription: {e}")
            raise ValueError(f"Failed to transcribe audio: {str(e)}")
    
    def _preprocess_audio(self, audio_data: bytes) -> bytes:
        """
        Preprocess audio data for better transcription results.
        
        Args:
            audio_data: Raw audio data bytes
            
        Returns:
            bytes: Processed audio data
        """
        try:
            # Create a temporary file to work with pydub
            with tempfile.NamedTemporaryFile(suffix=".webm") as temp_file:
                temp_file.write(audio_data)
                temp_file.flush()
                
                # Load audio with pydub
                audio = AudioSegment.from_file(temp_file.name)
                
                # Normalize audio levels
                audio = normalize(audio)
                
                # Convert to mono if stereo
                if audio.channels > 1:
                    audio = audio.set_channels(1)
                
                # Ensure sample rate is 48kHz (common for web audio)
                audio = audio.set_frame_rate(48000)
                
                # Export as WAV for better compatibility with Speech API
                buffer = io.BytesIO()
                audio.export(buffer, format="wav")
                return buffer.getvalue()
                
        except Exception as e:
            print(f"Warning: Audio preprocessing failed, using original data: {e}")
            return audio_data
    
    async def transcribe_audio_streaming(self, audio_stream) -> str:
        """
        Transcribe streaming audio data (placeholder for future implementation).
        
        Args:
            audio_stream: Streaming audio data
            
        Returns:
            str: Transcribed text
        """
        # This is a placeholder for streaming transcription
        # Implementation would depend on the specific streaming requirements
        raise NotImplementedError("Streaming transcription is not yet implemented")


# Create a global instance
voice_service = VoiceService()


async def transcribe_audio(voice_request: VoiceRequest) -> TranscriptionResponse:
    """
    Convenience function for transcribing audio.
    
    Args:
        voice_request: The voice request containing audio data
        
    Returns:
        TranscriptionResponse: The transcription result
    """
    return await voice_service.transcribe_audio(voice_request) 
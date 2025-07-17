# app/tts.py
import io
import logging
import asyncio
from typing import Optional
import edge_tts
import tempfile
import os


async def async_synthesize_speech(text: str, voice: str = "en-US-JennyNeural") -> bytes:
    """
    Async version: Synthesize speech using Edge TTS
    
    Args:
        text: Text to synthesize
        voice: Voice model, defaults to en-US-JennyNeural
        
    Returns:
        bytes: WAV format audio data
    """
    print(f"🔧 [EDGE TTS CORE] Starting synthesis for: '{text[:30]}...' with voice: {voice}")
    
    # Create temporary file to store audio
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
        tmp_path = tmp_file.name
    
    print(f"📁 [EDGE TTS CORE] Using temp file: {tmp_path}")
    
    try:
        # Use Edge TTS to generate audio, explicitly specify WAV format
        print(f"⚙️ [EDGE TTS CORE] Creating Edge TTS Communicate object...")
        
        # Create temporary MP3 file (Edge TTS native format)
        mp3_path = tmp_path.replace('.wav', '.mp3')
        
        communicate = edge_tts.Communicate(text, voice)
        
        print(f"💾 [EDGE TTS CORE] Saving audio to MP3...")
        await communicate.save(mp3_path)
        
        print(f"🔄 [EDGE TTS CORE] Converting MP3 to WAV...")
        
        # Use pydub to convert MP3 to WAV
        try:
            from pydub import AudioSegment
            
            # Load MP3 file
            audio = AudioSegment.from_mp3(mp3_path)
            
            # Convert to WAV and set standard parameters
            audio = audio.set_frame_rate(22050)  # Set standard sample rate
            audio = audio.set_channels(1)        # Mono
            audio = audio.set_sample_width(2)    # 16-bit depth
            
            # Export as WAV
            audio.export(tmp_path, format="wav")
            
            print(f"✅ [EDGE TTS CORE] Successfully converted to WAV")
            
            # Clean up temporary MP3 file
            import os
            if os.path.exists(mp3_path):
                os.unlink(mp3_path)
                
        except ImportError:
            print(f"❌ [EDGE TTS CORE] pydub not available, using direct MP3 output")
            # If pydub is not available, directly rename the file
            import shutil
            shutil.move(mp3_path, tmp_path)
        
        # Read the generated audio file
        print(f"📖 [EDGE TTS CORE] Reading generated audio file...")
        with open(tmp_path, 'rb') as f:
            audio_data = f.read()
        
        print(f"✅ [EDGE TTS CORE] Successfully generated audio: {len(audio_data)} bytes")
        return audio_data
    except Exception as e:
        print(f"❌ [EDGE TTS CORE] ERROR during synthesis: {e}")
        import traceback
        traceback.print_exc()
        raise e
    finally:
        # Clean up temporary files
        if os.path.exists(tmp_path):
            print(f"🗑️ [EDGE TTS CORE] Cleaning up temp file: {tmp_path}")
            os.unlink(tmp_path)
        else:
            print(f"⚠️ [EDGE TTS CORE] Temp file not found for cleanup: {tmp_path}")


def synthesize_speech(text: str, voice: str = "en-US-JennyNeural") -> bytes:
    """
    Sync version: Synthesize speech using Edge TTS (for testing and non-async environments)
    
    Args:
        text: Text to synthesize
        voice: Voice model, defaults to en-US-JennyNeural
        
    Returns:
        bytes: WAV format audio data
    """
    # Check if already in an event loop
    try:
        # If already in a running event loop, we cannot use run_until_complete
        loop = asyncio.get_running_loop()
        # If we reach here, we're in an async environment, should use async version
        raise RuntimeError("Cannot call synchronous synthesize_speech from async context. Use async_synthesize_speech instead.")
    except RuntimeError:
        # No running event loop, can create a new one
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(async_synthesize_speech(text, voice))


async def async_safe_synthesize_speech(text: str, voice: str = "en-US-JennyNeural") -> Optional[bytes]:
    """
    Async version: Safely handle TTS synthesis, automatically handle empty or invalid text
    Returns None if text is too short or invalid
    
    Args:
        text: Text to synthesize
        voice: Voice model, defaults to en-US-JennyNeural
        
    Returns:
        Optional[bytes]: WAV format audio data, None if failed
    """
    cleaned_text = text.strip()
    print(f"🎤 [EDGE TTS] Processing text: '{cleaned_text[:50]}...', length: {len(cleaned_text)}")
    
    if not cleaned_text or len(cleaned_text) < 2 or not any(c.isalnum() for c in cleaned_text):
        print(f"⏩ [EDGE TTS] Skipping TTS: content too short or non-verbal → '{cleaned_text}'")
        return None

    try:
        if len(cleaned_text) > 300:
             print(f"⏩ [EDGE TTS] Skipping TTS: content too long > 300 chars → '{cleaned_text[:50]}...'")
             return None
        
        # Intelligently select voice based on text content
        voice_to_use = _detect_language_and_voice(cleaned_text, voice)
        print(f"🗣️ [EDGE TTS] Using voice: {voice_to_use}")
        
        result = await async_synthesize_speech(cleaned_text, voice_to_use)
        print(f"✅ [EDGE TTS] Success: Generated {len(result) if result else 0} bytes")
        return result
        
    except Exception as e:
        print(f"❌ [EDGE TTS] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def safe_synthesize_speech(text: str, voice: str = "en-US-JennyNeural") -> Optional[bytes]:
    """
    Sync version: Safely handle TTS synthesis, automatically handle empty or invalid text
    Returns None if text is too short or invalid (for testing and non-async environments)
    
    Args:
        text: Text to synthesize
        voice: Voice model, defaults to en-US-JennyNeural
        
    Returns:
        Optional[bytes]: WAV format audio data, None if failed
    """
    cleaned_text = text.strip()
    
    if not cleaned_text or len(cleaned_text) < 2 or not any(c.isalnum() for c in cleaned_text):
        logging.warning(f"⏩ Skipping TTS: content too short or non-verbal → '{cleaned_text}'")
        return None

    try:
        if len(cleaned_text) > 300:
             logging.warning(f"⏩ Skipping TTS: content too long > 300 chars → '{cleaned_text[:50]}...'")
             return None
        
        # Intelligently select voice based on text content
        voice_to_use = _detect_language_and_voice(cleaned_text, voice)
        return synthesize_speech(cleaned_text, voice_to_use)
        
    except Exception as e:
        logging.error(f"❌ TTS synthesis failed for: '{cleaned_text}' → {e}")
        return None


def _detect_language_and_voice(text: str, default_voice: str = "en-US-JennyNeural") -> str:
    """
    Detect language based on text content and select appropriate voice
    
    Args:
        text: Input text
        default_voice: Default voice
        
    Returns:
        str: Selected voice model
    """
    # Simple language detection logic
    chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
    german_keywords = ['der', 'die', 'das', 'und', 'ist', 'von', 'zu', 'mit', 'auf']
    
    if chinese_chars > len(text) * 0.3:  # If Chinese characters exceed 30%
        return "zh-CN-XiaoxiaoNeural"  # Chinese female voice
    elif any(word.lower() in text.lower() for word in german_keywords):
        return "de-DE-KatjaNeural"  # German female voice
    else:
        return default_voice  # Default English voice


# For backward compatibility, provide some common voice options - using most natural Neural voices
VOICE_OPTIONS = {
    "english": "en-US-JennyNeural",        # Very natural female voice
    "chinese": "zh-CN-XiaoxiaoNeural",     # Chinese female voice
    "german": "de-DE-KatjaNeural",         # German female voice
    "english_male": "en-US-GuyNeural",     # Natural English male voice
    "chinese_male": "zh-CN-YunxiNeural",   # Chinese male voice
    "german_male": "de-DE-ConradNeural"    # German male voice
}


async def get_available_voices():
    """
    Get all available Edge TTS voices
    """
    voices = await edge_tts.list_voices()
    return voices

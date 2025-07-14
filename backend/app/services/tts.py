# app/tts.py
import io
import logging
from typing import Optional
import soundfile as sf
from TTS.api import TTS
import collections


from torch.serialization import add_safe_globals
from TTS.utils.radam import RAdam
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import XttsAudioConfig, XttsArgs
from TTS.config.shared_configs import BaseDatasetConfig

# 💡 add_safe_globals
add_safe_globals([RAdam])
add_safe_globals([collections.defaultdict, dict])
add_safe_globals([XttsConfig, XttsAudioConfig, BaseDatasetConfig, XttsArgs])

# Initialize the TTS model
tts_model = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False)

def synthesize_speech(text: str) -> bytes:
    # 1. generate waveform using TTS model
    waveform = tts_model.tts(text)

    # 2. Write to memory buffer and save as WAV format
    buf = io.BytesIO()
    sample_rate = tts_model.synthesizer.output_sample_rate if hasattr(tts_model, "synthesizer") and tts_model.synthesizer and hasattr(tts_model.synthesizer, "output_sample_rate") else 22050
    sf.write(buf, waveform, samplerate=sample_rate, format="WAV")
    buf.seek(0)

    # 3. Return bytes data for base64 encoding
    return buf.read()


def safe_synthesize_speech(text: str) -> Optional[bytes]:
    """
    Automatically handle empty or invalid text for TTS synthesis.
    Returns None if the text is too short or invalid.
    """
    cleaned_text = text.strip()
    
    if not cleaned_text or len(cleaned_text) < 2 or not any(c.isalnum() for c in cleaned_text):
        logging.warning(f"⏩ Skipping TTS: content too short or non-verbal → '{cleaned_text}'")
        return None

    try:
        if len(cleaned_text) > 300:
             logging.warning(f"⏩ Skipping TTS: content too long > 300 chars → '{cleaned_text[:50]}...'")
             return None
        return synthesize_speech(cleaned_text)
    except Exception as e:
        logging.error(f"❌ TTS synthesis failed for: '{cleaned_text}' → {e}")
        return None

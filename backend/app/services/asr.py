from faster_whisper import WhisperModel
import numpy as np

model = WhisperModel("base", device="cpu", compute_type="float32")

def transcribe(audio: np.ndarray, sample_rate=16000):
    print(f"🎙️ [WHISPER] Starting transcription with CPU mode")
    print(f"📊 [WHISPER] Audio shape: {audio.shape}, sample_rate: {sample_rate}")
    
    try:
        segments, info = model.transcribe(audio, beam_size=5)
        
        # Collect all text segments
        text_segments = []
        for seg in segments:
            print(f"📝 [WHISPER] Segment: '{seg.text}' (confidence: {getattr(seg, 'avg_logprob', 'N/A')})")
            text_segments.append(seg.text)
        
        full_text = " ".join(text_segments)
        language = info.language
        
        print(f"✅ [WHISPER] Transcription complete!")
        print(f"📄 [WHISPER] Full text: '{full_text}'")
        print(f"🌐 [WHISPER] Detected language: {language}")
        print(f"📈 [WHISPER] Language probability: {getattr(info, 'language_probability', 'N/A')}")
        
        return full_text, language
        
    except Exception as e:
        print(f"❌ [WHISPER] Transcription failed: {e}")
        import traceback
        traceback.print_exc()
        raise e

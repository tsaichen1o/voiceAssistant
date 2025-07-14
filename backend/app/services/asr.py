from faster_whisper import WhisperModel
import numpy as np

model = WhisperModel("base", compute_type="float32")

def transcribe(audio: np.ndarray, sample_rate=16000):   
    segments, info = model.transcribe(audio, beam_size=5)
    return " ".join([seg.text for seg in segments]), info.language

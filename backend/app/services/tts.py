import logging
import io
import re
import warnings
from pathlib import Path
from typing import Optional

import torch
import torchaudio
from huggingface_hub import snapshot_download
from speechbrain.inference.TTS import FastSpeech2
from speechbrain.inference.vocoders import HIFIGAN

device = "cuda" if torch.cuda.is_available() else "cpu" # `cuda` or `cpu`
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Suppress specific warnings from SpeechBrain
warnings.filterwarnings(
    "ignore",
    message="TextEncoder.expect_len was never called: assuming category count of .*",
    category=UserWarning,
)

FASTSPEECH2_REPO = "speechbrain/tts-fastspeech2-ljspeech"
FASTSPEECH2_DIR  = "pretrained_models/tts-fastspeech2-ljspeech"
HIFIGAN_REPO     = "speechbrain/tts-hifigan-libritts-16kHz"
HIFIGAN_DIR      = "pretrained_models/tts-hifigan-libritts-16kHz"

def is_model_cached(model_dir: str, files: list[str]) -> bool:
    return all(Path(model_dir, f).exists() for f in files)

try:
    if not is_model_cached(FASTSPEECH2_DIR, ["hyperparams.yaml","model.ckpt"]):
        logging.info("⬇️ Downloading FastSpeech2…")
        snapshot_download(FASTSPEECH2_REPO, local_dir=FASTSPEECH2_DIR, local_dir_use_symlinks=False)
    if not is_model_cached(HIFIGAN_DIR, ["hyperparams.yaml","generator.ckpt"]):
        logging.info("⬇️ Downloading HiFi‑GAN…")
        snapshot_download(HIFIGAN_REPO, local_dir=HIFIGAN_DIR,    local_dir_use_symlinks=False)

    tts_model     = FastSpeech2.from_hparams(source=FASTSPEECH2_DIR, savedir=FASTSPEECH2_DIR, run_opts={"device":device})
    vocoder_model = HIFIGAN   .from_hparams(source=HIFIGAN_DIR,    savedir=HIFIGAN_DIR,    run_opts={"device":device})

    logging.info("✅ Models loaded successfully.")

except Exception as e:
    logging.error(f"❌ Failed to load models: {e}")
    tts_model = vocoder_model = None


def synthesize_speech(text: str) -> bytes:
    if not tts_model or not vocoder_model:
        raise RuntimeError("Models not loaded.")

    # FastSpeech2(text) returns (mel, durations, pitch, energy)
    mel_output, _, _, _ = tts_model(text)
    # squeeze batch dimension → [n_mels, time]
    mel_spec = mel_output.squeeze(0).to(device)

    wav = vocoder_model.decode_batch(mel_spec).squeeze(0).cpu()

    buf = io.BytesIO()
    torchaudio.save(buf, wav.unsqueeze(0), sample_rate=16000, format="wav") # maybe you can change the sample rate on your computer, i tried 16000 and 22050, both do not work
    buf.seek(0)
    return buf.read()

def safe_synthesize_speech(text: str) -> Optional[bytes]:
    cleaned = text.strip()
    if len(cleaned) < 4 or not any(c.isalnum() for c in cleaned):
        logging.warning(f"⏩ Skipping invalid text: {cleaned!r}")
        return None
    cleaned = re.sub(r"[^\w\s.,!?\"'“”‘’]+", "", cleaned)
    try:
        return synthesize_speech(cleaned)
    except Exception as ee:
        logging.error(f"❌ TTS failed for {cleaned!r}: {ee}")
        return None

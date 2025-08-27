"""
Audio helpers: stream mic frames, record WAVs, and play confirmation beeps.
"""
from __future__ import annotations
import queue
import math
import os
import subprocess
from typing import Iterator

import numpy as np
import sounddevice as sd
import soundfile as sf

try:
    import simpleaudio  # type: ignore
    _HAS_SIMPLEAUDIO = True
except Exception:
    _HAS_SIMPLEAUDIO = False


def list_devices() -> None:
    """Prints available audio devices for debugging."""
    print(sd.query_devices())


def stream_frames(sample_rate: int, frame_ms: int, device: str | int = "default") -> Iterator[np.ndarray]:
    """
    Yields int16 mono frames of length `frame_ms` from the selected mic.

    Args:
        sample_rate: Target sample rate, e.g. 16000.
        frame_ms: Frame size in milliseconds, e.g. 30.
        device: sounddevice device name or index.
    """
    q: queue.Queue[np.ndarray] = queue.Queue()
    frame_len = int(sample_rate * (frame_ms / 1000.0))

    def callback(indata, frames, time, status):
        if status:
            print("[audio] status:", status, flush=True)
        q.put(indata.copy())

    with sd.InputStream(
        samplerate=sample_rate,
        channels=1,
        dtype="int16",
        blocksize=frame_len,
        device=device,
        callback=callback,
    ):
        while True:
            data = q.get()
            yield data.reshape(-1)


def record_seconds(seconds: float, sample_rate: int, device: str | int = "default") -> np.ndarray:
    """
    Records mono audio for a fixed duration and returns int16 samples.

    Args:
        seconds: Duration to record.
        sample_rate: Sample rate, e.g. 16000.
        device: sounddevice device.

    Returns:
        Numpy array of int16 samples.
    """
    frames = int(seconds * sample_rate)
    data = sd.rec(frames, samplerate=sample_rate, channels=1, dtype="int16", device=device)
    sd.wait()
    return data.reshape(-1)


def write_wav(path: str, samples: np.ndarray, sample_rate: int) -> None:
    """Writes int16 samples to a PCM16 WAV file."""
    sf.write(path, samples.astype(np.int16), sample_rate, subtype="PCM_16")


# --- Confirmation sound utilities (pure local) ---

def play_confirm_sound(path: str | None = None, vol: float = 0.25, duration: float = 0.12, sr: int = 16000) -> None:
    """
    Plays a short confirmation tone. If `path` is provided and exists, try to play it.
    Otherwise synthesize a sine 'beep' locally via simpleaudio if available.

    Args:
        path: Optional WAV file path to play.
        vol:  Linear volume (0..1) for synthesized beep.
        duration: beep length in seconds.
        sr:  sample rate for synthesized beep.
    """
    # If a WAV asset is supplied, try ffplay (if available) to avoid extra deps
    if isinstance(path, str) and os.path.isfile(path):
        try:
            subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path], check=False)
            return
        except Exception:
            pass

    if not _HAS_SIMPLEAUDIO:
        return  # silent fallback if simpleaudio isn't installed

    # Synthesize a short sine (880Hz)
    freq = 880.0
    n = int(sr * duration)
    t = np.arange(n, dtype=np.float32) / sr
    wave = (vol * np.sin(2 * math.pi * freq * t)).astype(np.float32)
    # convert to int16
    pcm = (wave * 32767).astype(np.int16)
    try:
        simpleaudio.play_buffer(pcm.tobytes(), 1, 2, sr)
    except Exception:
        pass

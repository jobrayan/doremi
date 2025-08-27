"""
WebRTC VAD gate to ignore silence/noise when processing.
"""
from __future__ import annotations
import numpy as np
import webrtcvad


class VADGate:
    """
    Simple VAD gate with fixed aggressiveness.

    Args:
        aggressiveness: 0..3 (3 = most aggressive).
        sample_rate: must be 8000, 16000, 32000, or 48000.
        frame_ms: one of {10, 20, 30}.
    """

    def __init__(self, aggressiveness: int = 2, sample_rate: int = 16000, frame_ms: int = 30):
        self.vad = webrtcvad.Vad(aggressiveness)
        self.sample_rate = sample_rate
        self.frame_len = int(sample_rate * (frame_ms / 1000.0))

    def is_speech(self, int16_frame: np.ndarray) -> bool:
        """Return True if frame is speech."""
        return self.vad.is_speech(int16_frame.tobytes(), self.sample_rate)

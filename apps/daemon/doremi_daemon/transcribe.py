"""
Local STT via faster-whisper.
"""
from __future__ import annotations
from typing import Any, Dict

from faster_whisper import WhisperModel


class LocalWhisper:
    """
    Thin wrapper around faster-whisper for synchronous transcription.

    Args:
        model_name: e.g. "tiny", "base", "small", "medium", "large-v3".
        compute_type: e.g. "int8", "int8_float16", "float16", "int8x4".
    """

    def __init__(self, model_name: str = "tiny", compute_type: str = "int8"):
        self.model = WhisperModel(model_name, compute_type=compute_type)

    def transcribe(self, wav_path: str) -> Dict[str, Any]:
        """
        Runs transcription and returns a simple JSON payload.
        """
        segments, info = self.model.transcribe(wav_path, beam_size=1)
        text = "".join([seg.text for seg in segments])
        return {
            "language": info.language,
            "duration": info.duration,
            "text": text.strip(),
        }

"""
Template-based wakeword with local enrollment (MFCC + cosine).
No cloud. Stores your "doremi" templates under templates/{label}_*.npz
"""
from __future__ import annotations
from pathlib import Path
from typing import List, Tuple

import librosa
import numpy as np
from numpy.typing import NDArray


def _mfcc(x: NDArray[np.float32], sr: int) -> NDArray[np.float32]:
    """
    Compute MFCCs for a mono float32 signal.

    Args:
        x: audio float32 mono [-1,1]
        sr: sample rate (e.g., 16000)

    Returns:
        (frames, coeffs) MFCC feature matrix
    """
    # Keep defaults small for speed; tune later if needed.
    F = librosa.feature.mfcc(y=x, sr=sr, n_mfcc=20, n_fft=512, hop_length=160)
    return F.astype(np.float32)


def _cosine(a: NDArray[np.float32], b: NDArray[np.float32]) -> float:
    """Cosine similarity between two vectors (flattened MFCCs)."""
    af = a.flatten()
    bf = b.flatten()
    na = np.linalg.norm(af) + 1e-9
    nb = np.linalg.norm(bf) + 1e-9
    return float(np.dot(af, bf) / (na * nb))


class TemplateWakeword:
    """
    Local template-based detector with user enrollment.

    Attributes:
        label: Wakeword label ("doremi").
        templates: List of enrolled MFCC templates.
        sr: Sample rate used for analysis.
        threshold: Cosine similarity threshold in [0,1].
    """

    def __init__(self, label: str, sr: int = 16000, threshold: float = 0.6, template_dir: str = "templates"):
        self.label = label
        self.sr = sr
        self.threshold = threshold
        self.dir = Path(template_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.templates: List[NDArray[np.float32]] = []
        self._load()

    def _load(self) -> None:
        """Loads all npz templates for the label from disk."""
        for p in sorted(self.dir.glob(f"{self.label}_*.npz")):
            data = np.load(p)
            self.templates.append(data["mfcc"].astype(np.float32))

    def enroll_from_float32(self, x: NDArray[np.float32]) -> Path:
        """
        Enroll a new sample (user says 'doremi'), store MFCC template.

        Args:
            x: Float32 mono samples at self.sr

        Returns:
            Path to saved template.
        """
        F = _mfcc(x, self.sr)
        idx = len(self.templates)
        out = self.dir / f"{self.label}_{idx:02d}.npz"
        np.savez_compressed(out, mfcc=F.astype(np.float32))
        self.templates.append(F.astype(np.float32))
        return out

    def detected(self, x: NDArray[np.float32]) -> Tuple[bool, float]:
        """
        Test a chunk for wakeword. We compute MFCC on the chunk and
        compare with each enrolled template via cosine similarity.

        Args:
            x: Float32 mono chunk

        Returns:
            (is_detected, best_score)
        """
        if not self.templates:
            return (False, 0.0)
        F = _mfcc(x, self.sr)
        scores = [_cosine(F, T) for T in self.templates]
        best = max(scores) if scores else 0.0
        return (best >= self.threshold, best)

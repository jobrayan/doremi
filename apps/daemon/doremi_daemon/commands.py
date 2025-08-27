"""
CommandRecognizer: local template-based short-command spotting.
Uses the same MFCC+cosine approach as wakeword enrollment.
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

from .hotword_template import _mfcc, _cosine


class CommandRecognizer:
    """
    Loads templates for multiple command labels (e.g., 'record','note','focus').
    Each label can have multiple samples (enrolled via CLI).

    Directory layout:
      templates/cmd_record_00.npz
      templates/cmd_record_01.npz
      templates/cmd_note_00.npz
      ...

    Args:
        sr: sample rate
        template_dir: template folder
        sensitivity: cosine threshold for acceptance
    """

    def __init__(self, sr: int = 16000, template_dir: str = "templates", sensitivity: float = 0.65):
        self.sr = sr
        self.dir = Path(template_dir)
        self.sensitivity = sensitivity
        self.db: Dict[str, List[np.ndarray]] = {}
        self._load()

    def _load(self) -> None:
        if not self.dir.exists():
            return
        for p in sorted(self.dir.glob("cmd_*.npz")):
            name = p.stem  # e.g., cmd_record_00
            parts = name.split("_")
            if len(parts) < 2:
                continue
            label = parts[1]  # 'record'
            F = np.load(p)["mfcc"].astype(np.float32)
            self.db.setdefault(label, []).append(F)

    def best_label(self, x_f32: np.ndarray) -> Tuple[str | None, float]:
        """
        Returns (label, score) for the best-matching command or (None, 0.0).
        """
        if not self.db:
            return (None, 0.0)
        F = _mfcc(x_f32, self.sr).astype(np.float32)
        best_label: str | None = None
        best_score: float = 0.0
        for label, templs in self.db.items():
            for T in templs:
                s = _cosine(F, T)
                if s > best_score:
                    best_score = s
                    best_label = label
        if best_label is None or best_score < self.sensitivity:
            return (None, best_score)
        return (best_label, best_score)

    def enroll_label_from_float32(self, label: str, x_f32: np.ndarray) -> Path:
        """
        Enroll a new command sample for 'label', writing templates/cmd_<label>_<N>.npz
        """
        self.dir.mkdir(parents=True, exist_ok=True)
        F = _mfcc(x_f32, self.sr).astype(np.float32)
        # count existing
        idx = len(list(self.dir.glob(f"cmd_{label}_*.npz")))
        out = self.dir / f"cmd_{label}_{idx:02d}.npz"
        np.savez_compressed(out, mfcc=F)
        # update db
        self.db.setdefault(label, []).append(F)
        return out

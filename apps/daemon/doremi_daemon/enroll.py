"""
CLI to enroll the 'doremi' wakeword by recording N samples from mic.
"""
from __future__ import annotations
import argparse
import time

import numpy as np

from .audio import record_seconds
from .hotword_template import TemplateWakeword


def int16_to_float32(x: np.ndarray) -> np.ndarray:
    return (x.astype(np.float32) / 32768.0).clip(-1.0, 1.0)


def main() -> None:
    """
    Record N samples and save as templates for the given label.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default="doremi")
    ap.add_argument("--samples", type=int, default=5)
    ap.add_argument("--seconds", type=float, default=1.2, help="length per utterance")
    ap.add_argument("--sr", type=int, default=16000)
    ap.add_argument("--device", default="default")
    ap.add_argument("--template-dir", default="templates")
    args = ap.parse_args()

    print(f"[enroll] Say '{args.label}' when prompted. We will capture {args.samples} samples.")
    tw = TemplateWakeword(args.label, sr=args.sr, template_dir=args.template_dir)

    for i in range(args.samples):
        input(f"Press Enter and then say '{args.label}' ({i+1}/{args.samples})…")
        samples = record_seconds(seconds=args.seconds, sample_rate=args.sr, device=args.device)
        x = int16_to_float32(samples)
        p = tw.enroll_from_float32(x)
        print(f"[enroll] saved: {p}")
        time.sleep(0.5)

    print("[enroll] done.")


if __name__ == "__main__":
    main()

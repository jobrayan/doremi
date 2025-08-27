"""
CLI to enroll short command templates (e.g., 'record','focus','note').
Saves templates as templates/cmd_<label>_<N>.npz
"""
from __future__ import annotations
import argparse
import time

import numpy as np

from .audio import record_seconds
from .commands import CommandRecognizer


def int16_to_float32(x: np.ndarray) -> np.ndarray:
    return (x.astype(np.float32) / 32768.0).clip(-1.0, 1.0)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("label", help="command label, e.g. record|focus|note|stop")
    ap.add_argument("--samples", type=int, default=5)
    ap.add_argument("--seconds", type=float, default=0.8, help="length per utterance")
    ap.add_argument("--sr", type=int, default=16000)
    ap.add_argument("--device", default="default")
    ap.add_argument("--template-dir", default="templates")
    args = ap.parse_args()

    print(f"[enroll-cmd] Say '{args.label}' when prompted. We will capture {args.samples} samples.")
    cr = CommandRecognizer(sr=args.sr, template_dir=args.template_dir)

    for i in range(args.samples):
        input(f"Press Enter and then say '{args.label}' ({i+1}/{args.samples})…")
        samples = record_seconds(seconds=args.seconds, sample_rate=args.sr, device=args.device)
        x = int16_to_float32(samples)
        p = cr.enroll_label_from_float32(args.label, x)
        print(f"[enroll-cmd] saved: {p}")
        time.sleep(0.4)

    print("[enroll-cmd] done.")


if __name__ == "__main__":
    main()

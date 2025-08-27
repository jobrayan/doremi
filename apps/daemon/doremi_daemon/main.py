"""
Doremi Daemon: template wakeword + actions + optional follow-command.
"""
from __future__ import annotations
import argparse
from typing import List

import numpy as np
import yaml

from .audio import stream_frames, play_confirm_sound
from .vad import VADGate
from .actions import dispatch
from .hotword_template import TemplateWakeword
from .commands import CommandRecognizer


def load_cfg(path: str) -> dict:
    """Loads YAML config from path."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


def int16_to_float32(x: np.ndarray) -> np.ndarray:
    """Converts int16 mono to float32 [-1, 1]."""
    return (x.astype(np.float32) / 32768.0).clip(-1.0, 1.0)


def is_ide_action(name: str) -> bool:
    return name.startswith("ide:")


def run_actions(names: List[str], actions_cfg: dict, device: str, sr: int) -> None:
    for name in names:
        dispatch(name, actions_cfg, device, sr)


def main() -> None:
    """
    CLI entrypoint for doremi.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--config", default="configs/doremi.yml", help="Path to YAML config.")
    args = ap.parse_args()

    cfg = load_cfg(args.config)

    mic_cfg = cfg.get("mic", {})
    device = mic_cfg.get("device", "default")
    sr = int(mic_cfg.get("sample_rate", 16000))
    frame_ms = int(mic_cfg.get("frame_ms", 30))

    # VAD
    vad_cfg = cfg.get("vad", {})
    vad = (
        VADGate(aggressiveness=int(vad_cfg.get("aggressiveness", 2)), sample_rate=sr, frame_ms=frame_ms)
        if vad_cfg.get("enabled", True)
        else None
    )

    # Wakeword
    ww_cfg = cfg.get("wakeword", {})
    label = ww_cfg.get("label", "doremi")
    sensitivity = float(ww_cfg.get("sensitivity", 0.6))
    template_dir = ww_cfg.get("enroll", {}).get("template_dir", "templates")
    detector = TemplateWakeword(label=label, sr=sr, threshold=sensitivity, template_dir=template_dir)
    if not detector.templates:
        print(f"[warn] no templates found for '{label}'. Run enrollment first.")

    # Follow-command
    fc_cfg = cfg.get("follow_command", {})
    fc_enabled = bool(fc_cfg.get("enabled", False))
    fc_window_sec = float(fc_cfg.get("window_seconds", 1.2))
    fc_threshold = float(fc_cfg.get("sensitivity", 0.65))
    fc_default = fc_cfg.get("default_on_uncertain", "ide:record")
    fc_map = fc_cfg.get("map", {})
    cmd_rec = CommandRecognizer(sr=sr, template_dir=template_dir, sensitivity=fc_threshold) if fc_enabled else None

    on_detect: List[str] = list(cfg.get("actions_on_detect", []))

    # Rolling buffer for wakeword analysis (~1.2s)
    buf_sec = 1.2
    max_len = int(sr * buf_sec)
    f32_buf = np.zeros((0,), dtype=np.float32)

    frames_iter = stream_frames(sample_rate=sr, frame_ms=frame_ms, device=device)
    print("[doremi] listening…")

    def append_buf(new_f32: np.ndarray) -> None:
        nonlocal f32_buf
        if f32_buf.size == 0:
            f32_buf = new_f32
        else:
            f32_buf = np.concatenate([f32_buf, new_f32])
        if f32_buf.size > max_len:
            f32_buf = f32_buf[-max_len:]

    while True:
        frame = next(frames_iter)
        if vad and not vad.is_speech(frame):
            continue
        f32 = int16_to_float32(frame)
        append_buf(f32)

        # Need enough audio for a decision
        if f32_buf.size < int(0.6 * sr):
            continue

        ok, score = detector.detected(f32_buf)
        if ok:
            print(f"[wake] '{label}' score={score:.2f}")

            if fc_enabled and cmd_rec is not None and cmd_rec.db:
                # Capture a short command window and classify using the existing stream
                needed_frames = int(np.ceil((fc_window_sec * 1000.0) / frame_ms))
                collected: list[np.ndarray] = []
                for _ in range(needed_frames):
                    next_frame = next(frames_iter)
                    # Do not VAD-gate this capture; we want the raw command window
                    collected.append(next_frame)
                cmd_int16 = np.concatenate(collected, axis=0).astype(np.int16)
                cmd_f32 = int16_to_float32(cmd_int16)
                lab, cscore = cmd_rec.best_label(cmd_f32)
                if lab is not None:
                    action_name = fc_map.get(lab)
                    print(f"[cmd] '{lab}' score={cscore:.2f} -> {action_name}")
                    if action_name:
                        if not is_ide_action(action_name):
                            play_confirm_sound()
                        dispatch(action_name, cfg.get("actions", {}), device, sr)
                    else:
                        # No mapping -> fallback
                        dispatch(fc_default, cfg.get("actions", {}), device, sr)
                else:
                    print(f"[cmd] uncertain score={cscore:.2f} -> default {fc_default}")
                    dispatch(fc_default, cfg.get("actions", {}), device, sr)
            else:
                # Run default pipeline
                run_actions(on_detect, cfg.get("actions", {}), device, sr)

            # Clear buffer after trigger to avoid immediate re-trigger
            f32_buf = np.zeros((0,), dtype=np.float32)


if __name__ == "__main__":
    main()

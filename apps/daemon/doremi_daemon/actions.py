"""
Action registry: builtin recorder+STT, system no-op, and companion bridge.
"""
from __future__ import annotations
import json
import subprocess
from typing import Any

from .audio import record_seconds, write_wav
from .transcribe import LocalWhisper


def run_companion(command: str, args: list[str]) -> int:
    """
    Spawns the TS companion CLI (Node) with a subcommand.

    Returns:
        Process exit code.
    """
    proc = subprocess.run(["node", "apps/companion/dist/index.js", command, *args])
    return proc.returncode


def action_companion(action_cfg: dict) -> None:
    cmd = action_cfg.get("command")
    args = action_cfg.get("args", [])
    if not cmd:
        print("[warn] companion action missing 'command'")
        return
    rc = run_companion(cmd, [str(a) for a in args])
    print(f"[companion] {cmd} exit={rc}")


def action_record_and_transcribe(cfg: dict, mic_device: str, sample_rate: int) -> None:
    """
    Records N seconds, writes WAV, runs local Whisper, dumps JSON (optional).
    """
    seconds = float(cfg.get("record_seconds", 20))
    out_wav = cfg.get("save_wav_to", "/tmp/doremi_last.wav")
    stt_cfg: dict[str, Any] = cfg.get("stt", {})
    model = stt_cfg.get("model", "tiny")
    compute_type = stt_cfg.get("compute_type", "int8")
    engine = stt_cfg.get("engine", "faster-whisper")

    print(f"[record] {seconds}s…")
    samples = record_seconds(seconds=seconds, sample_rate=sample_rate, device=mic_device)
    write_wav(out_wav, samples, sample_rate)

    if engine == "faster-whisper":
        print(f"[stt] model={model} compute={compute_type}")
        whisper = LocalWhisper(model, compute_type)
        res = whisper.transcribe(out_wav)
    else:
        res = {"text": "", "language": "unknown", "duration": 0}

    out_json = stt_cfg.get("output_json")
    if out_json:
        with open(out_json, "w") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
    print("[stt] text:", res.get("text", ""))


def action_system_noop(_: dict) -> None:
    print("[system] noop")


def dispatch(action_name: str, actions_cfg: dict, mic_device: str, sample_rate: int) -> None:
    """
    Lookup and run the action by name.
    """
    action = actions_cfg.get(action_name)
    if not action:
        print(f"[warn] no action '{action_name}'")
        return

    kind = action.get("kind", "builtin")

    if kind == "companion":
        action_companion(action)
    elif kind == "builtin" and action_name == "record-and-transcribe":
        action_record_and_transcribe(action, mic_device, sample_rate)
    elif action_name.startswith("system:"):
        action_system_noop(action)
    else:
        print(f"[warn] unsupported action {action_name} kind={kind}")

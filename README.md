# doremi (Do·Re·Mi)

Local, open-source wakeword daemon for Ubuntu. Say “doremi” to focus your project window and start IDE voice record (Windsurf by default). Optional follow-command mode lets you say a quick command right after the wake word (e.g., “record”, “focus”, “note”). No audio leaves your machine.

- Privacy-first: all wakeword + command spotting is local (MFCC templates)
- Lightweight: CPU-friendly template matching; optional STT via faster-whisper
- Editor-friendly: focuses your project window and sends hotkeys


## Repository layout

- `configs/` – example YAML config
- `apps/daemon/` – Python daemon (`doremi_daemon`)
- `apps/companion/` – TypeScript companion CLI (wmctrl/xdotool)
- `system/` – systemd user service unit


## Requirements

Ubuntu (X11 recommended for xdotool/wmctrl)
- System packages: `python3-venv` `libsndfile1` `ffmpeg` `xdotool` `wmctrl`
- Python 3.10+
- Node 18+

Wayland: xdotool/wmctrl don’t work reliably. Use `ydotool`/`wtype` as alternatives (not yet wired in).


## Install (local dev)

```bash
# System deps
sudo apt update
sudo apt install -y python3-venv libsndfile1 ffmpeg xdotool wmctrl

# In this repo
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e apps/daemon

# Node companion
cd apps/companion
npm i
npm run build
cd -

# Config
cp configs/doremi.example.yml configs/doremi.yml
# Edit configs/doremi.yml:
# - actions.project:focus.args --project "/path/to/your/project"
# - keep ide hotkey default: ctrl+shift+m (Windsurf/VS Code)
```


## Enrollment (one-time)
Enroll the wakeword “doremi” and optionally short commands.

```bash
# Wakeword (say “doremi” when prompted)
python3 -m doremi_daemon.enroll --label doremi --samples 5 --seconds 1.2

# Optional commands (say label as prompted)
python3 -m doremi_daemon.enroll_cmd record --samples 5 --seconds 0.8
python3 -m doremi_daemon.enroll_cmd focus  --samples 5 --seconds 0.8
python3 -m doremi_daemon.enroll_cmd note   --samples 5 --seconds 0.8
```

Templates are stored under `templates/` as compressed MFCC features.


## Run

Foreground (good for testing):
```bash
python3 -m doremi_daemon.main -c configs/doremi.yml
```

Systemd user service (recommended):
```bash
# Install to /opt/doremi if you want a global location (optional)
sudo mkdir -p /opt/doremi && sudo chown "$USER":"$USER" /opt/doremi
rsync -a --exclude .venv ./ /opt/doremi/
python3 -m venv /opt/doremi/.venv
/opt/doremi/.venv/bin/pip install -U pip
/opt/doremi/.venv/bin/pip install -e /opt/doremi/apps/daemon
cd /opt/doremi/apps/companion && npm i && npm run build && cd -
cp /opt/doremi/configs/doremi.example.yml /opt/doremi/configs/doremi.yml

# user-level unit
mkdir -p ~/.config/systemd/user
cp system/doremi.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now doremi.service
journalctl --user -u doremi.service -f
```


## Configuration (YAML)
See `configs/doremi.example.yml`.

Key sections:
- `mic`: device, sample rate, frame size
- `wakeword`: template engine, label “doremi”, sensitivity, template_dir
- `follow_command`: enables a short listening window after the wake word
  - map labels → actions, e.g., `record` → `ide:record`
  - default_on_uncertain: falls back to IDE record
- `actions_on_detect`: actions run when follow-command is disabled or skipped
- `actions`: action registry
  - `project:focus` uses companion to raise your project window
  - `ide:record` sends Ctrl+Shift+M (Windsurf/VS Code default)
  - `record-and-transcribe` records N seconds and runs local faster-whisper


## Behavior
- Default IDE: Windsurf. We send `ctrl+shift+m` via xdotool.
- Confirmation beep: plays only for non-IDE actions (e.g., `note`).
- Privacy: all wakeword/command detection is local; STT is local if you enable it.

Tuning:
- If false triggers, raise sensitivity (e.g., wakeword 0.7–0.8).
- If misses, lower (e.g., 0.5–0.55).


## Wayland note
xdotool/wmctrl require X11. On Wayland, replace with `ydotool` or `wtype` and adapt `apps/companion` accordingly.


## License
MIT — see `LICENSE`.

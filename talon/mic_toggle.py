"""Watch /tmp/talon-mic-toggle and sync Talon's speech state to actual mic volume.

Pairs with the Karabiner right-shift double-tap + mic-toggle.sh. Drop this into
your Talon user directory alongside sketchybar_bridge.py.

Flow: Karabiner → mic-toggle.sh flips input volume & touches signal file →
this watcher reads the new volume → speech.enable() or .disable() accordingly →
Talon mode changes → sketchybar_bridge.py propagates to the bar.
"""

import os
import subprocess

from talon import actions, fs

SIGNAL_FILE = "/tmp/talon-mic-toggle"

# Create the signal file on first load so fs.watch has something to watch.
if not os.path.exists(SIGNAL_FILE):
    open(SIGNAL_FILE, "w").close()


def get_mic_volume() -> int:
    """Return macOS input volume (0–100), or -1 on failure."""
    try:
        result = subprocess.run(
            ["/usr/bin/osascript", "-e", "input volume of (get volume settings)"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        return int(result.stdout.strip())
    except Exception:
        return -1


def on_signal(path: str, flags) -> None:
    if path != SIGNAL_FILE:
        return
    vol = get_mic_volume()
    if vol < 0:
        return
    if vol > 0:
        actions.speech.enable()
    else:
        actions.speech.disable()


fs.watch(os.path.dirname(SIGNAL_FILE), on_signal)

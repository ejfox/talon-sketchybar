"""Push Talon mode changes to sketchybar via --trigger events.

Drop this into your Talon user directory (e.g. ~/.talon/user/sketchybar/).
Pair it with the sketchybar `talon_state` event subscription and `talon.sh` plugin.

Fires on every Talon context update (the same hook Talon itself uses to repaint
its mode canvases). Non-blocking subprocess — never stalls Talon's speech loop.
"""

import subprocess
from talon import app, registry, scope

# Absolute path required — Talon's embedded Python has a minimal PATH.
# Adjust if your sketchybar binary lives elsewhere (Apple Silicon default below).
SKETCHYBAR = "/opt/homebrew/bin/sketchybar"

# Custom sketchybar event name. Match this in your sketchybarrc:
#   sketchybar --add event talon_state
#   sketchybar --subscribe <item_name> talon_state
EVENT = "talon_state"

last_mode = None


def current_mode() -> str:
    """Map Talon's active modes to a single, sketchybar-friendly label.

    Returned values: sleep | command | dictation | mixed | other
    """
    modes = scope.get("mode") or set()
    if "sleep" in modes:
        return "sleep"
    if "dictation" in modes and "command" in modes:
        return "mixed"
    if "dictation" in modes:
        return "dictation"
    if "command" in modes:
        return "command"
    return "other"


def push(mode: str) -> None:
    """Fire a sketchybar trigger with MODE=<mode> in the environment.

    Fire-and-forget: start_new_session detaches the child so a slow sketchybar
    never blocks Talon; stdout/stderr → DEVNULL suppresses ResourceWarning noise.
    """
    subprocess.Popen(
        [SKETCHYBAR, "--trigger", EVENT, f"MODE={mode}"],
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def on_update_contexts() -> None:
    """Debounced callback — only push when the mode actually changed."""
    global last_mode
    mode = current_mode()
    if mode != last_mode:
        last_mode = mode
        push(mode)


def on_ready() -> None:
    registry.register("update_contexts", on_update_contexts)
    # Emit current state once at startup so sketchybar isn't stuck on stale data.
    on_update_contexts()


app.register("ready", on_ready)

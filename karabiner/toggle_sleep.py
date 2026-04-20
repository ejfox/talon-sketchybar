"""Action to toggle Talon between sleep and command mode.

Pair with `toggle_sleep.talon` (the F19 binding) and the Karabiner
double-shift complex modification. The bridge picks up the mode change
automatically — no extra plumbing required.
"""

from talon import Module, actions, scope

mod = Module()


@mod.action_class
class Actions:
    def talon_sleep_toggle():
        """Toggle Talon sleep mode (sleep ↔ command)."""
        modes = scope.get("mode") or set()
        if "sleep" in modes:
            actions.mode.disable("sleep")
            actions.mode.enable("command")
        else:
            actions.mode.enable("sleep")
            actions.mode.disable("command")

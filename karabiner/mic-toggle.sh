#!/bin/bash
# Toggle macOS input volume and poke Talon to sync its speech state.
# Invoked by Karabiner on double-tap right_shift (see right-shift-toggle.json).
#
# Flow:
#   1. Flip macOS input volume between 0 and 100
#   2. Touch a signal file that Talon's mic_toggle.py watches
#   3. Talon's watcher reads the new volume and calls speech.enable() or .disable()
#   4. Talon's mode changes → sketchybar_bridge.py picks it up → bar updates
#
# No sketchybar trigger is needed from here — the bridge handles the bar.

IV=$(/usr/bin/osascript -e 'input volume of (get volume settings)')
if [ "$IV" -gt 0 ]; then
  /usr/bin/osascript -e 'set volume input volume 0'
else
  /usr/bin/osascript -e 'set volume input volume 100'
fi
/usr/bin/touch /tmp/talon-mic-toggle

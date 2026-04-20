# talon-sketchybar

Push [Talon Voice](https://talonvoice.com) state into [sketchybar](https://github.com/FelixKratz/SketchyBar) — event-driven, zero-polling, ~60 lines of Python.

When Talon's mode changes (sleep, command, dictation, mixed), a sketchybar item updates instantly on the same hook Talon uses to repaint its own mode indicators. No `osascript` polling, no signal files, no daemons.

## Why

The common "mic on" sketchybar recipe polls `osascript -e 'input volume of (get volume settings)'` every few seconds. It's coarse, laggy, and measures the wrong thing — macOS input volume ≠ Talon listening state. This bridge fixes that:

- **Zero latency.** Fires the instant Talon's context graph updates.
- **Zero polling.** Pure event-driven; sketchybar sleeps until Talon speaks.
- **Accurate.** Reflects Talon modes (`sleep`, `command`, `dictation`, `mixed`), not raw mic volume.
- **Arbitrary payload.** Ship any scope data (current app, active `.talon` files, mic gain) via env vars if you want.

## Install

### 1. Talon side

Copy `talon/sketchybar_bridge.py` into your Talon user directory:

```bash
mkdir -p ~/.talon/user/sketchybar
cp talon/sketchybar_bridge.py ~/.talon/user/sketchybar/
```

Talon auto-reloads Python files on save — no restart needed. Confirm in `~/.talon/talon.log`:

```
DEBUG [+] /Users/you/.talon/user/sketchybar/sketchybar_bridge.py
```

### 2. Sketchybar side

Copy the plugin:

```bash
cp sketchybar/plugins/talon.sh ~/.config/sketchybar/plugins/
chmod +x ~/.config/sketchybar/plugins/talon.sh
```

Paste `sketchybar/sketchybarrc.snippet` into your `~/.config/sketchybar/sketchybarrc` (the snippet registers the custom event, adds the item, subscribes it to `talon_state`, and points at the plugin).

Reload sketchybar:

```bash
brew services restart sketchybar
```

### 3. Test it

```bash
# Manually fire a state change from the shell:
sketchybar --trigger talon_state MODE=command   # pink "TALON" appears
sketchybar --trigger talon_state MODE=sleep     # item hides
```

If that works, Talon is already driving the bar — try saying `talon sleep` and `talon wake` and watch the bar react.

## Bonus: double-tap right-shift to toggle Talon (Karabiner-Elements)

A hands-free gesture: double-tap **right shift** to mute the mic (which also puts Talon to sleep) and double-tap again to unmute (which wakes Talon). The sketchybar item updates automatically because the bridge catches Talon's mode change — no extra plumbing.

The flow has four pieces:

```
Karabiner (double-tap right_shift)
    │
    ▼  shell_command
mic-toggle.sh  (flips input volume 0↔100, touches /tmp/talon-mic-toggle)
    │
    ▼  fs.watch
Talon mic_toggle.py  (reads new volume, calls speech.enable/.disable)
    │
    ▼  mode change → update_contexts
sketchybar_bridge.py  (already installed from the main section above)
    │
    ▼  sketchybar --trigger
bar updates
```

### 1. Install the mic-toggle script

```bash
mkdir -p ~/bin
cp karabiner/mic-toggle.sh ~/bin/mic-toggle
chmod +x ~/bin/mic-toggle
```

Quick check it works:

```bash
~/bin/mic-toggle    # mic flips; run twice to confirm both directions
```

### 2. Install the Talon watcher

```bash
cp talon/mic_toggle.py ~/.talon/user/sketchybar/
```

Talon auto-loads it. The watcher reacts to any touch of `/tmp/talon-mic-toggle`.

### 3. Install the Karabiner rule

Karabiner doesn't have a "import from file" button — local rules live in `~/.config/karabiner/assets/complex_modifications/`:

```bash
mkdir -p ~/.config/karabiner/assets/complex_modifications
cp karabiner/right-shift-toggle.json ~/.config/karabiner/assets/complex_modifications/
```

Then in the Karabiner-Elements app: **Complex Modifications → Add predefined rule → Enable** the "Double-tap right shift → toggle mic" rule.

(The rule's `shell_command` path is `$HOME/bin/mic-toggle` — adjust if you installed the script elsewhere.)

### Verify

1. Double-tap right shift. Mic should mute (input volume → 0) and Talon should stop responding to voice.
2. The bar item should hide (Talon's speech is disabled, so no command mode).
3. Double-tap again. Mic unmutes, Talon resumes, bar pill reappears.
4. If nothing fires, open Karabiner EventViewer and confirm two right-shift presses within ~300ms trigger the rule.

## Customizing

Everything interesting is in two places:

- **`talon/sketchybar_bridge.py`** — `current_mode()` maps Talon scope to labels. Add anything `scope.get(...)` returns (current app, `.talon` tags, mic gain) and pass it as additional env vars in `push()`.
- **`sketchybar/plugins/talon.sh`** — pure `case` statement on `$MODE`. Change the icon, color, glyph, or add conditions on other env vars. Uses [sketchybar's standard item API](https://felixkratz.github.io/SketchyBar/config/items).

## How it works

```
┌──────────────┐       update_contexts        ┌──────────────────────┐
│    Talon     │──────────────────────────────▶│ sketchybar_bridge.py │
└──────────────┘                                └──────────┬───────────┘
                                                           │ subprocess.Popen
                                                           │ sketchybar --trigger
                                                           ▼
                                              ┌────────────────────────┐
                                              │  sketchybar talon_state │
                                              └──────────┬──────────────┘
                                                         │ MODE=command
                                                         ▼
                                                ┌────────────────┐
                                                │   talon.sh     │ ──▶ bar updates
                                                └────────────────┘
```

The bridge hooks Talon's `registry.register("update_contexts", ...)` — the same synchronous callback that Talon itself uses to repaint its mode canvases. When the mode changes, it shells out to `sketchybar --trigger talon_state MODE=<mode>` with `Popen(start_new_session=True)` so a slow sketchybar never stalls Talon's speech loop.

On the sketchybar side, the item is subscribed to the custom `talon_state` event. When triggered, sketchybar runs `talon.sh` with `$MODE` in its environment. The plugin does a simple `case` match and styles the item.

## License

MIT. See `LICENSE`.

## Credits

Prior art referenced while designing this:

- [chaosparrot/talon_hud](https://github.com/chaosparrot/talon_hud) — in-Talon HUD, same scope primitives
- [talonhub/community](https://github.com/talonhub/community) — canonical mode definitions
- [SketchyBar discussion #12](https://github.com/FelixKratz/SketchyBar/discussions/12) — the yabai-signal custom event pattern this borrows

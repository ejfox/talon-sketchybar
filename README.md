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

## Bonus: double-tap shift to toggle Talon (Karabiner-Elements)

Uses Karabiner to turn a double-tap of left shift into an F19 keypress, which Talon binds to a sleep toggle. Result: tap-tap and the bar lights up or dims.

**Why F19?** It's a dead key on every macOS keyboard — never emitted accidentally — so binding it globally in Talon is safe. Karabiner is the translator; Talon is the consumer.

### Install the Karabiner rule

Open **Karabiner-Elements → Complex Modifications → Add rule → Import more rules from the Internet**, or merge `karabiner/double-shift.json` into `~/.config/karabiner/karabiner.json` under `complex_modifications.rules`.

Quick import:

```bash
open -a Karabiner-Elements
# then: Preferences → Complex Modifications → Add rule → Import
#       point at karabiner/double-shift.json
```

### Install the Talon binding

```bash
cp karabiner/toggle_sleep.talon ~/.talon/user/sketchybar/
cp karabiner/toggle_sleep.py    ~/.talon/user/sketchybar/
```

`toggle_sleep.py` defines `user.talon_sleep_toggle()` and `toggle_sleep.talon` binds F19 → that action globally. When the action fires, Talon's mode changes → `sketchybar_bridge.py` catches it → the bar updates. All one atomic chain.

### Verify

1. Press shift-shift rapidly. The bar should toggle between hidden and a pink `TALON` pill.
2. If nothing happens, check Karabiner's EventViewer (double-tap should emit F19).
3. If F19 fires but Talon doesn't toggle, verify `talon sleep toggle` works manually by voice first.

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

#!/bin/bash
# Sketchybar plugin for Talon state.
# Invoked by the `talon_state` event fired from sketchybar_bridge.py.
#
# The bridge sets $MODE to one of: sleep | command | dictation | mixed | other
# Adjust icons, colors, and visibility below to taste.
#
# Default color palette mirrors Talon's community mode convention:
#   command    → pink    (#e60067) — listening for commands
#   dictation  → teal    (#6eedf7) — transcribing speech
#   mixed      → teal    (#6eedf7) — command + dictation together
#   sleep      → hidden
#   other      → hidden

case "${MODE:-other}" in
  command)
    sketchybar --set "$NAME" \
      drawing=on \
      icon="TALON" \
      icon.color=0xffe60067
    ;;
  dictation)
    sketchybar --set "$NAME" \
      drawing=on \
      icon="DICT" \
      icon.color=0xff6eedf7
    ;;
  mixed)
    sketchybar --set "$NAME" \
      drawing=on \
      icon="MIX" \
      icon.color=0xff6eedf7
    ;;
  sleep|*)
    sketchybar --set "$NAME" drawing=off
    ;;
esac

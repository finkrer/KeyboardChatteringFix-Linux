#!/bin/bash
# ==============================================================================
# MOUSE CHATTERING FIX - STARTUP SCRIPT
# ==============================================================================
# Change the `cd` path below to the absolute path of this project folder.
# Ensure this script is executable: chmod +x mouse_chattering.sh
#
# AVAILABLE ARGUMENTS:
#  -m "usb-id-here"            : The device ID of your mouse in /dev/input/by-id/
#  -t 30                       : Button double-click threshold in ms (Default: 30)
#  --buttons BTN_LEFT,BTN_SIDE : Explicitly filter only these buttons (Leave blank for all)
#
# ADVANCED SENSOR ARGUMENTS:
#  -sr 150                     : Block scroll wheel jumping in reverse direction (ms)
#  -sd 30                      : Block scroll wheel firing twice in same direction (ms)
#  -jl 300                     : Block massive cursor teleports exceeding X pixels per frame
#
#  -r                          : Enable auto-reconnect infinite loop (Required for Cron/SysVinit)
#                                DO NOT USE `-r` if using Systemd! Systemd handles restarts natively.
# ==============================================================================

cd /absolute/path/to/project && sudo python3 -m src.mouse_main -m <MOUSE id> -t 30

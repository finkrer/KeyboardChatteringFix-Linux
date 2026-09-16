#!/bin/bash
# ==============================================================================
# KEYBOARD CHATTERING FIX - STARTUP SCRIPT
# ==============================================================================
# Change the `cd` path below to the absolute path of this project folder.
# Ensure this script is executable: chmod +x keyboard_chattering.sh
#
# AVAILABLE ARGUMENTS:
#  -k "usb-id-here"         : The device ID of your keyboard in /dev/input/by-id/
#  -t 30                    : Bounce filter threshold in milliseconds (Default: 30)
#  --keys KEY_A,KEY_SPACE   : Explicitly filter only these keys (Leave blank for all)
#  -r                       : Enable auto-reconnect infinite loop (Required for Cron/SysVinit)
#                             DO NOT USE `-r` if using Systemd! Systemd handles restarts natively.
# ==============================================================================

cd /absolute/path/to/project && sudo python3 -m src.keyboard_main -k <KEYBOARD id> -t 30

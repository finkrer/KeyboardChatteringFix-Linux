"""
Constants for mouse chattering filter configuration.

PRECEDENCE RULES:
1. Command Line (--buttons / -m): Highest priority. If provided, this file is ignored.
2. This File: Used if no command line argument is provided.
3. Interactive Prompt: Used ONLY if both CLI and this file are empty.
"""
import libevdev

# ==========================================
# 0. DEFAULT DEVICE
# ==========================================
# Set this to avoid the interactive prompt on boot/startup. 
# Leave as "" to be asked every time if running manually.
# Example: DEVICE_NAME = "usb-Logitech_Gaming_Mouse-event-mouse"
DEVICE_NAME = ""

# ==========================================
# 1. SPECIFIC BUTTON FILTERING (Allowlist)
# ==========================================
# To filter specific buttons, add them to this set. 
# Example: FILTERED_BUTTONS = {"BTN_LEFT", "BTN_SIDE"}
# Leave it empty as set() to filter ALL mouse buttons by default.
FILTERED_BUTTONS = set()

# ==========================================
# 2. SCROLL AXIS FILTERING (Allowlist)
# ==========================================
# To filter specific scroll directions, add their libevdev codes to this set.
# Leave it empty as set() to filter ALL scroll axes by default.
# Example: If your Logitech MX horizontal wheel glitches, but vertical is fine:
# FILTERED_SCROLL_AXES = {"REL_HWHEEL", "REL_HWHEEL_HI_RES"}
FILTERED_SCROLL_AXES = set()

# ==========================================
# 3. PER-BUTTON THRESHOLDS
# ==========================================
# Override the default threshold for specific buttons.
BUTTON_THRESHOLDS = {
    # "BTN_LEFT": 30,
    # "BTN_SIDE": 50,
}

# ==========================================
# 4. BUTTON REMAPPING / MACROS
# ==========================================
# Swap buttons at the kernel level. Format: {"BUTTON_PRESSED": "BUTTON_OUTPUT"}
BUTTON_MAP = {
    # "BTN_SIDE": "BTN_MIDDLE", # Example: Make a side thumb button act as a middle click
}


# ==========================================
# REFERENCE: COMMON MOUSE BUTTON & AXIS VALUES
# ==========================================
# Standard Clicks:
# BTN_LEFT    (Standard Left Click)
# BTN_RIGHT   (Standard Right Click)
# BTN_MIDDLE  (Scroll Wheel Click)
#
# Side / Gaming Buttons (Thumb buttons):
# BTN_SIDE    (Often defaults to "Back" in browsers)
# BTN_EXTRA   (Often defaults to "Forward" in browsers)
# BTN_FORWARD (Alternative Forward)
# BTN_BACK    (Alternative Back)
# BTN_TASK    (Sometimes used for DPI shifts or task views)
#
# Numbered Extra Buttons (For MMO mice like Razer Naga / Corsair Scimitar):
# BTN_0, BTN_1, BTN_2, BTN_3, BTN_4, BTN_5, BTN_6, BTN_7, BTN_8, BTN_9
#
# Scroll Axes:
# REL_WHEEL          (Standard Vertical Scroll)
# REL_HWHEEL         (Standard Horizontal Scroll)
# REL_WHEEL_HI_RES   (High-Resolution Vertical Scroll)
# REL_HWHEEL_HI_RES  (High-Resolution Horizontal Scroll)

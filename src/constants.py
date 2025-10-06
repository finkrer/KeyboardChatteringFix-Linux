"""
Constants for keyboard chattering filter configuration.

DEFAULT BEHAVIOR:
- If FILTERED_KEYS is empty (None or empty list), ALL keys will be filtered (original behavior)
- If FILTERED_KEYS contains keys, only those specific keys will be filtered

To customize which keys should be filtered, define the FILTERED_KEYS list with key names.
Use only the key name (e.g., "KEY_A", "KEY_SPACE") instead of the full code.

Examples of key names:
- Letters: "KEY_A", "KEY_B", "KEY_C", etc.
- Numbers: "KEY_0", "KEY_1", "KEY_2", etc.
- Special: "KEY_SPACE", "KEY_ENTER", "KEY_BACKSPACE", "KEY_TAB"
- Function: "KEY_F1", "KEY_F2", etc.
- Modifiers: "KEY_LEFTSHIFT", "KEY_RIGHTSHIFT", "KEY_LEFTCTRL", etc.
- Arrows: "KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT"
"""

from typing import Optional, Set

# KEY FILTERING CONFIGURATION

FILTERED_KEYS = {
    # Example: filter only some letters that have chattering
    "KEY_P",
}

# Option 1: Filter ALL keys (original default behavior)
# Leave as None or empty list to maintain original behavior
# FILTERED_KEYS: Optional[Set[str]] = None

# Option 2: Filter only specific keys
# Uncomment and modify the list below to filter only specific keys
# FILTERED_KEYS = {
#     # Example: filter only some letters that have chattering
#     "KEY_A",
#     "KEY_S",
#     "KEY_D",
#     "KEY_SPACE",
#     "KEY_ENTER",
# }

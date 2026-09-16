import logging
from collections import defaultdict
from typing import DefaultDict, Dict, NoReturn, List
import time
import libevdev

def filter_chattering(evdev: libevdev.Device, default_threshold: int, keys_to_filter: List[libevdev.EventCode], 
                      key_thresholds: dict, key_map: dict) -> NoReturn:
    
    # Reset global states on reconnect to prevent ghost "stuck" keys
    _last_key_up.clear()
    _key_pressed.clear()

    time.sleep(1) # Delay to allow Enter key to release natively after running script
    evdev.grab()
    ui_dev = evdev.create_uinput_device()
    logging.info("Listening to keyboard input events...")

    while True:
        try:
            for e in evdev.events():
                # Process the event. _from_keystroke returns either the (modified) event, or None to drop it.
                processed_event = _from_keystroke(e, default_threshold, keys_to_filter, key_thresholds, key_map)
                if processed_event:
                    ui_dev.send_events([processed_event, libevdev.InputEvent(libevdev.EV_SYN.SYN_REPORT, 0)])
        except libevdev.EventsDroppedException:
            # If the user presses too many keys simultaneously (NKRO overflow), resync the buffer
            logging.debug("Kernel buffer overflowed. Resyncing...")
            for e in evdev.sync():
                processed_event = _from_keystroke(e, default_threshold, keys_to_filter, key_thresholds, key_map)
                if processed_event:
                    ui_dev.send_events([processed_event, libevdev.InputEvent(libevdev.EV_SYN.SYN_REPORT, 0)])

def _from_keystroke(event: libevdev.InputEvent, default_threshold: int, keys_to_filter: List[libevdev.EventCode], 
                    key_thresholds: dict, key_map: dict):
    
    # Ignore sync/misc events natively
    if event.matches(libevdev.EV_SYN) or event.matches(libevdev.EV_MSC):
        return None

    # REMAPPING: Safely construct a brand new event object to prevent mutating C-bindings
    if event.matches(libevdev.EV_KEY) and event.code.name in key_map:
        target_key_name = key_map[event.code.name]
        event = libevdev.InputEvent(libevdev.evbit(target_key_name), event.value, event.sec, event.usec)
        if event.value == 1: # Only log on the key-down to prevent log spam
            logging.debug(f'REMAPPED to {target_key_name}')

    # Do not filter modifier combinations or natively held keys (value > 1)
    if not event.matches(libevdev.EV_KEY) or event.value > 1:
        return event

    # If an allowlist is provided and this key isn't in it, forward it without filtering
    if keys_to_filter and event.code not in keys_to_filter:
        return event

    # PER-KEY THRESHOLDS: Check if this specific key has a custom delay, else use default.
    threshold = key_thresholds.get(event.code.name, default_threshold)

    # Process standard Key Up (0) events
    if event.value == 0:
        if _key_pressed[event.code]:
            logging.debug(f'FORWARDING {event.code.name} up')
            _last_key_up[event.code] = event.sec * 1E6 + event.usec
            _key_pressed[event.code] = False
            return event
        else:
            return None

    prev = _last_key_up.get(event.code)
    now = event.sec * 1E6 + event.usec

    # Check time since last key up event for this specific key
    if prev is None or now - prev > threshold * 1E3:
        logging.debug(f'FORWARDING {event.code.name} down')
        _key_pressed[event.code] = True
        return event

    logging.info(f'FILTERED {event.code.name} down: bounced within {threshold}ms')
    return None

_last_key_up: Dict[libevdev.EventCode, int] = {}
_key_pressed: DefaultDict[libevdev.EventCode, bool] = defaultdict(bool)

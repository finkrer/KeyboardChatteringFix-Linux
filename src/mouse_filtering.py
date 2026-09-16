import logging
from collections import defaultdict
from typing import DefaultDict, Dict, NoReturn, List
import time
import libevdev

def filter_mouse_chattering(evdev: libevdev.Device, default_threshold: int, scroll_rev_threshold: int, 
                            scroll_interval: int, jump_limit: int,
                            buttons_to_filter: List[libevdev.EventCode], scroll_axes_to_filter: List[libevdev.EventCode], 
                            btn_thresholds: dict, btn_map: dict) -> NoReturn:
    
    # Reset global states on reconnect to prevent ghost "stuck" buttons
    global _last_btn_code
    _last_btn_up.clear()
    _btn_pressed.clear()
    _last_btn_code = None
    _last_scroll_time.clear()
    _last_scroll_dir.clear()

    time.sleep(1)
    evdev.grab()
    ui_dev = evdev.create_uinput_device()
    logging.info("Listening to mouse events...")

    while True:
        try:
            for e in evdev.events():
                processed_event = _from_event(e, default_threshold, scroll_rev_threshold, scroll_interval, jump_limit, 
                                              buttons_to_filter, scroll_axes_to_filter, btn_thresholds, btn_map)
                if processed_event:
                    ui_dev.send_events([processed_event, libevdev.InputEvent(libevdev.EV_SYN.SYN_REPORT, 0)])
                    
        except libevdev.EventsDroppedException:
            # High-polling-rate gaming mice (1000Hz+) can overflow the kernel buffer.
            # We catch the exception, resync the buffer, and process the recovered events natively.
            logging.debug("Kernel buffer overflowed (high polling rate). Resyncing...")
            for e in evdev.sync():
                processed_event = _from_event(e, default_threshold, scroll_rev_threshold, scroll_interval, jump_limit, 
                                              buttons_to_filter, scroll_axes_to_filter, btn_thresholds, btn_map)
                if processed_event:
                    ui_dev.send_events([processed_event, libevdev.InputEvent(libevdev.EV_SYN.SYN_REPORT, 0)])

def _from_event(event: libevdev.InputEvent, default_threshold: int, scroll_rev_threshold: int, scroll_interval: int,
                jump_limit: int, buttons_to_filter: List[libevdev.EventCode], 
                scroll_axes_to_filter: List[libevdev.EventCode], btn_thresholds: dict, btn_map: dict):
    global _last_btn_code
    
    if event.matches(libevdev.EV_SYN) or event.matches(libevdev.EV_MSC):
        return None

    # === SCROLL & MOVEMENT (EV_REL) ===
    if event.matches(libevdev.EV_REL):
        # 1. Jump filtering for Cursor X/Y
        if event.code in (libevdev.EV_REL.REL_X, libevdev.EV_REL.REL_Y):
            if jump_limit > 0 and abs(event.value) >= jump_limit:
                logging.warning(f"BLOCKED TELEPORT: Cursor jumped {event.value} pixels in 1 frame!")
                return None 
            return event

        # 2. Scroll Wheel Filtering
        if event.code in (libevdev.EV_REL.REL_WHEEL, libevdev.EV_REL.REL_HWHEEL,
                          libevdev.EV_REL.REL_WHEEL_HI_RES, libevdev.EV_REL.REL_HWHEEL_HI_RES):
            
            if scroll_axes_to_filter and event.code not in scroll_axes_to_filter:
                return event

            axis = event.code
            now = event.sec * 1E6 + event.usec
            direction = 1 if event.value > 0 else -1

            last_time = _last_scroll_time.get(axis)
            last_dir = _last_scroll_dir.get(axis)

            # Scroll Reverse Glitch (Faulty encoder bouncing backwards)
            if last_dir != direction and last_time is not None:
                if scroll_rev_threshold > 0 and (now - last_time) < scroll_rev_threshold * 1E3:
                    logging.info(f"BLOCKED REVERSE SCROLL: Encoder glitched backwards!")
                    return None

            # Scroll Double-Action (Worn encoder firing twice in the same direction)
            if last_dir == direction and last_time is not None:
                if scroll_interval > 0 and (now - last_time) < scroll_interval * 1E3:
                    logging.info(f"BLOCKED DOUBLE-SCROLL: Same direction too fast!")
                    return None

            _last_scroll_time[axis] = now
            _last_scroll_dir[axis] = direction
            return event
            
        return event

    # === BUTTON CLICKS (EV_KEY) ===
    # REMAPPING: Safely construct a brand new event object
    if event.matches(libevdev.EV_KEY) and event.code.name in btn_map:
        target_btn = btn_map[event.code.name]
        event = libevdev.InputEvent(libevdev.evbit(target_btn), event.value, event.sec, event.usec)
        if event.value == 1:
            logging.debug(f'REMAPPED to {target_btn}')

    # Do not filter Native held clicks (value > 1) or Absolute movement (EV_ABS)
    if event.matches(libevdev.EV_ABS) or not event.matches(libevdev.EV_KEY) or event.value > 1:
        return event

    if buttons_to_filter and event.code not in buttons_to_filter:
        return event

    # Check for custom button threshold, fallback to default
    threshold = btn_thresholds.get(event.code.name, default_threshold)

    # Process Button Up (0)
    if event.value == 0:
        if _btn_pressed[event.code]:
            _last_btn_up[event.code] = event.sec * 1E6 + event.usec
            _btn_pressed[event.code] = False
            return event
        return None

    prev = _last_btn_up.get(event.code)
    now = event.sec * 1E6 + event.usec

    # Check _last_btn_code to allow fast alternating clicks (e.g. Left -> Right -> Left)
    if prev is None or now - prev > threshold * 1E3 or _last_btn_code != event.code:
        _btn_pressed[event.code] = True
        _last_btn_code = event.code
        return event

    logging.info(f'FILTERED {event.code.name} double-click!')
    return None

_last_btn_up: Dict[libevdev.EventCode, int] = {}
_btn_pressed: DefaultDict[libevdev.EventCode, bool] = defaultdict(bool)
_last_btn_code = None
_last_scroll_time: Dict[libevdev.EventCode, int] = {}
_last_scroll_dir: Dict[libevdev.EventCode, int] = {}

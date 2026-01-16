import logging
from collections import defaultdict
from typing import DefaultDict, Dict, NoReturn, Set

import libevdev

from src.constants import FILTERED_KEYS


def _get_filtered_keys_set() -> Set[libevdev.EventCode]:
    """
    Converts the list of key names to libevdev codes.
    If FILTERED_KEYS is None or empty, returns None (filter all keys).
    """
    if not FILTERED_KEYS:
        return None

    filtered_codes = set()
    for key_name in FILTERED_KEYS:
        try:
            # Converts "KEY_A" to libevdev.EV_KEY.KEY_A
            key_code = getattr(libevdev.EV_KEY, key_name)
            filtered_codes.add(key_code)
        except AttributeError:
            logging.warning(f"Key name '{key_name}' not found in libevdev.EV_KEY. Skipping...")

    return filtered_codes


# Converts the key list once at initialization
_FILTERED_KEYS_CODES = _get_filtered_keys_set()


def filter_chattering(evdev: libevdev.Device, threshold: int) -> NoReturn:
    # grab the device - now only we see the events it emits
    evdev.grab()
    # create a copy of the device that we can write to - this will emit the filtered events to anyone who listens
    ui_dev = evdev.create_uinput_device()

    # Log filtering mode
    if _FILTERED_KEYS_CODES is None:
        logging.info("Filtering mode: ALL keys (original behavior)")
    else:
        logging.info(f"Filtering mode: SPECIFIC keys only ({len(_FILTERED_KEYS_CODES)} keys configured)")
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            key_names = [name for name in FILTERED_KEYS]
            logging.debug(f"Filtered keys: {', '.join(sorted(key_names))}")

    logging.info("Listening to input events...")

    while True:
        # since the descriptor is blocking, this blocks until there are events available
        for e in evdev.events():
            if _from_keystroke(e, threshold):
                ui_dev.send_events([e, libevdev.InputEvent(libevdev.EV_SYN.SYN_REPORT, 0)])


def _from_keystroke(event: libevdev.InputEvent, threshold: int) -> bool:
    # no need to relay those - we are going to emit our own
    if event.matches(libevdev.EV_SYN) or event.matches(libevdev.EV_MSC):
        return False

    # some events we don't want to filter, like EV_LED for toggling NumLock and the like, and also key hold events
    if not event.matches(libevdev.EV_KEY) or event.value > 1:
        logging.debug(f'FORWARDING {event.code}')
        return True

    if _FILTERED_KEYS_CODES is not None and event.code not in _FILTERED_KEYS_CODES:
        logging.debug(f'FORWARDING {event.code} (not in filtered keys list)')
        return True

    # the values are 0 for up, 1 for down and 2 for hold
    if event.value == 0:
        if _key_pressed[event.code]:
            logging.debug(f'FORWARDING {event.code} up')
            _last_key_up[event.code] = event.sec * 1E6 + event.usec
            _key_pressed[event.code] = False
            return True
        else:
            logging.info(f'FILTERING {event.code} up: key not pressed beforehand')
            return False

    prev = _last_key_up.get(event.code)
    now = event.sec * 1E6 + event.usec

    if prev is None or now - prev > threshold * 1E3:
        logging.debug(f'FORWARDING {event.code} down')
        _key_pressed[event.code] = True
        return True

    logging.info(
        f'FILTERED {event.code} down: last key up event happened {(now - prev) / 1E3} ms ago')
    return False


_last_key_up: Dict[libevdev.EventCode, int] = {}
_key_pressed: DefaultDict[libevdev.EventCode, bool] = defaultdict(bool)

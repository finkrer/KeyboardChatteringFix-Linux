#!/usr/bin/env python3

from collections import defaultdict
import sys
from typing import Callable, DefaultDict, Dict, NoReturn, Union
import libevdev
from libevdev import Device, InputEvent
from libevdev.const import EventCode
from contextlib import contextmanager
import time
import logging

logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                    format='[%(levelname)s] %(message)s')


threshold = 0


@contextmanager
def get_device(device_path: str) -> Device:
    """Safely get an evdev device handle."""

    fd = open(device_path, 'rb')
    evdev = Device(fd)
    try:
        yield evdev
    finally:
        fd.close()


def start_filtering(evdev: Device, filter: Callable[[InputEvent], Union[InputEvent, None]]) -> NoReturn:
    """Start filtering input from a device."""

    # grab the device to ourselves - now only we see the events it emits
    evdev.grab()
    # create a copy of the device that we can write to - this will emit the filtered events to anyone who listens
    uidev = evdev.create_uinput_device()

    while True:
        # since the descriptor is blocking, this blocks until there are events available
        for e in evdev.events():
            if (f := filter(e)) is not None:
                send_event_packet(uidev, f)


def send_event_packet(device: Device, event: InputEvent):
    """Send an event packet properly ending with a SYN_REPORT."""

    packet = [event, InputEvent(libevdev.EV_SYN.SYN_REPORT, 0)]
    device.send_events(packet)


last_key_up: Dict[EventCode, int] = dict()
key_pressed: DefaultDict[EventCode, bool] = defaultdict(bool)


def filter_chatter(event: InputEvent) -> Union[InputEvent, None]:
    """Filter input events that are coming too fast"""

    # no need to relay those - we are going to emit our own
    if event.matches(libevdev.EV_SYN) or event.matches(libevdev.EV_MSC):
        logging.debug(f'Got {event.code} - filtering')
        return None

    # some events we don't want to filter, like EV_LED for toggling NumLock and the like, and also key hold events
    if not event.matches(libevdev.EV_KEY) or event.value > 1:
        logging.debug(f'Got {event.code} - letting through')
        return event

    # the values are 0 for up, 1 for down and 2 for hold
    if event.value == 0 and not key_pressed[event.code]:
        logging.debug(
            f'Got {event.code} up, but key is not pressed - filtering')
        return None

    if event.value == 0 and key_pressed[event.code]:
        logging.debug(f'Got {event.code} up - letting through')
        last_key_up[event.code] = event.sec * 1E6 + event.usec
        key_pressed[event.code] = False
        return event

    prev = last_key_up.get(event.code)
    now = event.sec * 1E6 + event.usec

    if prev is None or now - prev > threshold * 1E3:
        logging.debug(f'Got {event.code} down - letting through')
        key_pressed[event.code] = True
        return event

    logging.debug(
        f'Got {event.code} down, but last key up was just {(now - prev) / 1E3} ms ago - filtering')
    return None


def main(args):
    global threshold
    path = args[1]
    threshold = int(args[2])

    with get_device(path) as d:
        start_filtering(d, filter_chatter)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: {} /dev/input/**/<device> <threshold>".format(sys.argv[0]))
        print("""    where the device is your keyboard's event device
    and the threshold is the minimal delay between a key up and a key down in ms""")
        sys.exit(1)

    # we don't want to (incompletely) capture stuff triggered by starting the script itself
    time.sleep(1)
    main(sys.argv)

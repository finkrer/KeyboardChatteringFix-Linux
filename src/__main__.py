import argparse
import logging
import sys
from contextlib import contextmanager

import libevdev

from src.filtering import filter_chattering
from src.keyboard_retrieval import retrieve_keyboard_name, INPUT_DEVICES_PATH, abs_keyboard_path


@contextmanager
def get_device_handle(keyboard_name: str) -> libevdev.Device:
    """ Safely get an evdev device handle. """

    fd = open(abs_keyboard_path(keyboard_name), 'rb')
    evdev = libevdev.Device(fd)
    try:
        yield evdev
    finally:
        fd.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-k', '--keyboard', type=str, default=str(),
                        help=f"Name of your chattering keyboard device as listed in {INPUT_DEVICES_PATH}. "
                             f"If left unset, will be attempted to be retrieved automatically.")
    parser.add_argument('-t', '--threshold', type=int, default=30, help="Filter time threshold in milliseconds. "
                                                                        "Default=30ms.")
    parser.add_argument('-v', '--verbosity', type=int, default=1, choices=[0, 1, 2])
    args = parser.parse_args()

    logging.basicConfig(
        level={
            0: logging.CRITICAL,
            1: logging.INFO,
            2: logging.DEBUG
        }[args.verbosity],
        handlers=[
            logging.StreamHandler(
                sys.stdout
            )
        ],
        format="%(asctime)s - %(message)s",
        datefmt="%H:%M:%S"
    )

    with get_device_handle(args.keyboard or retrieve_keyboard_name()) as device:
        filter_chattering(device, args.threshold)

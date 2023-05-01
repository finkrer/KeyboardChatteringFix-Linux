#!/usr/bin/env python3

import argparse
import logging
import sys
from contextlib import contextmanager

import libevdev

from src.filtering import filter_chattering
from src.keyboard_retrieval import retrieve_keyboard_path


@contextmanager
def get_device_handle(device_path: str) -> libevdev.Device:
    """ Safely get an evdev device handle. """

    fd = open(device_path, 'rb')
    evdev = libevdev.Device(fd)
    try:
        yield evdev
    finally:
        fd.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path', type=str, default=str())
    parser.add_argument('-t', '--threshold', type=int, default=30)
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
        format="%(asctime)s %(message)s - ",
        datefmt="%H:%M:%S"
    )

    with get_device_handle(args.path or retrieve_keyboard_path()) as device:
        filter_chattering(device, args.threshold)
import argparse
import logging
import sys
from contextlib import contextmanager

import libevdev

from src.filtering import filter_chattering
from src.keyboard_retrieval import (
    INPUT_DEVICES_PATH,
    abs_keyboard_path,
    create_config_file,
    parse_config_file,
    retrieve_keyboard_name,
)


@contextmanager
def get_device_handle(keyboard_name: str) -> libevdev.Device:
    """Safely get an evdev device handle."""

    fd = open(abs_keyboard_path(keyboard_name), "rb")
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
    parser.add_argument('-t', '--threshold', type=int, default=None, help="Filter time threshold in milliseconds. "
                                                                        "Default=30ms.")
    parser.add_argument('-v', '--verbosity', type=int, default=1, choices=[0, 1, 2])
    parser.add_argument('-c', '--config', type=str, default='config.yaml', help="Path to the configuration file.")
    parser.add_argument('-n', '--new-config', action='store_true', help="Create a new configuration file at the path "
                                                                        "defined by --config.")
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
        datefmt="%H:%M:%S",
    )

    # Load the config file if it exists.
    try:
        with open(args.config, "r") as file:
            config = parse_config_file(file)
            logging.info(f"Using configuration from {args.config}.")
            logging.debug(f"Configuration: {config}")
    except FileNotFoundError:
        config = {}

    # Use common threshold from the config if it was specified.
    # Otherwise, use the default value of 30 ms.
    if "default" not in config:
        config["default"] = 30

    # Allow overriding the threshold from the command line.
    if args.threshold is not None:
        config["default"] = args.threshold
        logging.info(f"Overriding default threshold with {args.threshold} ms from command line.")

    with get_device_handle(args.keyboard or retrieve_keyboard_name()) as device:
        if args.new_config:
            create_config_file(device, args.config, default_threshold=config["default"])
            logging.info(f"New configuration file created at {args.config}.")
        filter_chattering(device, config)

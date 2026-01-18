import logging
import os
import shutil
from io import TextIOWrapper
from typing import Final

import libevdev
import yaml

INPUT_DEVICES_PATH: Final = "/dev/input/by-id"
_KEYBOARD_NAME_SUFFIX: Final = "-kbd"


def retrieve_keyboard_name() -> str:
    keyboard_devices = list(filter(lambda d: d.endswith(_KEYBOARD_NAME_SUFFIX), os.listdir(INPUT_DEVICES_PATH)))
    n_devices = len(keyboard_devices)

    if n_devices == 0:
        raise ValueError(f"Couldn't find a keyboard in '{INPUT_DEVICES_PATH}'")
    if n_devices == 1:
        logging.info(f"Found keyboard: {keyboard_devices[0]}")
        return keyboard_devices[0]

    # Use native Python input for user selection
    print("Select a device:")
    for idx, device in enumerate(keyboard_devices, start=1):
        print(f"{idx}. {device}")

    selected_idx = -1
    while selected_idx < 1 or selected_idx > n_devices:
        try:
            selected_idx = int(input("Enter your choice (number): "))
            if selected_idx < 1 or selected_idx > n_devices:
                print(f"Please select a number between 1 and {n_devices}")
        except ValueError:
            print("Please enter a valid number")

    return keyboard_devices[selected_idx - 1]


def abs_keyboard_path(device: str) -> str:
    return os.path.join(INPUT_DEVICES_PATH, device)


def create_config_file(device: libevdev.Device, config_path: str, default_threshold: int) -> None:
    # Create a new configuration file with the default threshold.
    with open(config_path, "w") as file:
        file.write(f"default: {default_threshold}\n")

        # Write each supported key event with the default threshold, but commented out.
        supported = device.evbits
        for event_type, event_codes in supported.items():
            if event_type == libevdev.EV_KEY:
                for event_code in event_codes:
                    file.write(f'# "{event_code.name}:{event_code.value}": {default_threshold}\n')

    # Get the current user who invoked sudo (e.g., $SUDO_USER).
    user = os.environ.get("SUDO_USER")
    if user is None:
        raise Exception("Script must be run with sudo.")

    # Change ownership to the invoking user.
    shutil.chown(config_path, user=user)

    # Set permissions (read/write for the user, read-only for others).
    os.chmod(config_path, 0o644)  # rw-r--r--


def parse_config_file(config_file: TextIOWrapper) -> dict:
    input_config = yaml.safe_load(config_file)

    # Convert the keys to EventCodes.
    config = {}
    for key, value in input_config.items():
        if key == "default":
            config[key] = value
        else:
            event_code = libevdev.evbit("EV_KEY", key.split(":")[0])
            config[event_code] = value

    return config

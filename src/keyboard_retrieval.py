import logging
import os
from typing import Final

import inquirer

INPUT_DEVICES_PATH: Final = '/dev/input/by-id'
_KEYBOARD_NAME_SUFFIX: Final = '-kbd'


def retrieve_keyboard_name() -> str:
    keyboard_devices = list(filter(lambda d: d.endswith(_KEYBOARD_NAME_SUFFIX), os.listdir(INPUT_DEVICES_PATH)))
    n_devices = len(keyboard_devices)

    if n_devices == 0:
        raise ValueError(f"Couldn't find a keyboard in '{INPUT_DEVICES_PATH}'")
    if n_devices == 1:
        logging.info(f"Found keyboard: {keyboard_devices[0]}")
        return keyboard_devices[0]
    return inquirer.prompt(
        questions=[
            inquirer.List(
                '_',
                message='Select a device',
                choices=keyboard_devices,
            ),
        ]
    ).values()[0]


def abs_keyboard_path(device: str) -> str:
    return os.path.join(INPUT_DEVICES_PATH, device)

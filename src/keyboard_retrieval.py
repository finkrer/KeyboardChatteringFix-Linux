import logging
import os

import inquirer

_INPUT_DEVICES_PATH = '/dev/input/by-id'


def retrieve_keyboard_path() -> str:
    keyboard_devices = list(filter(lambda d: d.endswith('-kbd'), os.listdir(_INPUT_DEVICES_PATH)))
    n_devices = len(keyboard_devices)

    if n_devices == 0:
        raise ValueError(f"Couldn't find a keyboard in '{_INPUT_DEVICES_PATH}'")
    if n_devices == 1:
        device = keyboard_devices[0]
        logging.info(f"Retrieved keyboard: {device}")
        return _abs_keyboard_path(device)
    else:
        return _abs_keyboard_path(
            inquirer.prompt(
                questions=[
                    inquirer.List(
                        '_',
                        message='Select a device',
                        choices=keyboard_devices,
                    ),
                ]
            ).values()[0]
        )


def _abs_keyboard_path(device: str) -> str:
    return os.path.join(_INPUT_DEVICES_PATH, device)

import logging
import os
from typing import Final

# Use 'by-id' because device names here are persistent across reboots/USB ports
INPUT_DEVICES_PATH: Final = '/dev/input/by-id'

def retrieve_mouse_name() -> str:
    """Lists all valid input devices and prompts the user to select one."""
    all_devices = os.listdir(INPUT_DEVICES_PATH)
    
    # We intentionally do NOT filter for the word 'mouse' here. 
    # Advanced gaming mice often split their macro buttons into virtual 
    # keyboard endpoints. Showing all '-event-' nodes ensures you can find it.
    valid_devices = [d for d in all_devices if '-event-' in d]
    device_list = list(set(valid_devices))
    n_devices = len(device_list)

    if n_devices == 0:
        raise ValueError(f"Couldn't find any devices in '{INPUT_DEVICES_PATH}'. Please provide it manually with -m.")

    print("Select a mouse device:")
    
    for idx, device in enumerate(sorted(device_list), start=1):
        print(f"{idx}. {device}")

    selected_idx = -1
    
    while selected_idx < 1 or selected_idx > n_devices:
        try:
            selected_idx = int(input("Enter your choice (number): "))
            if selected_idx < 1 or selected_idx > n_devices:
                print(f"Please select a number between 1 and {n_devices}")
        except ValueError:
            print("Please enter a valid number")

    sorted_devices = sorted(device_list)
    return sorted_devices[selected_idx - 1]

def abs_mouse_path(device: str) -> str:
    return os.path.join(INPUT_DEVICES_PATH, device)

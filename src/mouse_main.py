import argparse
import logging
import sys
import os
import time
import libevdev

from src.mouse_filtering import filter_mouse_chattering
from src.mouse_retrieval import retrieve_mouse_name, INPUT_DEVICES_PATH, abs_mouse_path

# Safely import the config file if it exists
try:
    from src.mouse_config import DEVICE_NAME, FILTERED_BUTTONS, FILTERED_SCROLL_AXES, BUTTON_THRESHOLDS, BUTTON_MAP
except ImportError:
    DEVICE_NAME, FILTERED_BUTTONS, FILTERED_SCROLL_AXES, BUTTON_THRESHOLDS, BUTTON_MAP = "", set(), set(), {}, {}

def parse_list(data_str):
    """Parses comma-separated CLI arguments into a list of strings."""
    if not data_str: return []
    return [d.strip() for d in data_str.split(',')]
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mouse', type=str, default=str())
    parser.add_argument('-t', '--threshold', type=int, default=30)
    parser.add_argument('-sr', '--scroll-reverse', type=int, default=0, help="Block scroll reversing directions (ms)")
    parser.add_argument('-sd', '--scroll-double', type=int, default=0, help="Block scroll same direction (ms)")
    parser.add_argument('-jl', '--jump-limit', type=int, default=0, help="Block teleporting cursor >= X pixels")
    parser.add_argument('-r', '--reconnect', action='store_true', help="Loop infinitely and wait for device reconnection instead of exiting")
    parser.add_argument('--buttons', type=parse_list, default=[])
    parser.add_argument('-v', '--verbosity', type=int, default=1, choices=[0, 1, 2])
    args = parser.parse_args()

    logging.basicConfig(level={0: logging.CRITICAL, 1: logging.INFO, 2: logging.DEBUG}[args.verbosity],
                        handlers=[logging.StreamHandler(sys.stdout)],
                        format="%(asctime)s - %(message)s", datefmt="%H:%M:%S")

    # PREVENT SILENT FAILURES: Validate config thresholds/maps at startup
    for btn_name in list(BUTTON_THRESHOLDS.keys()):
        try:
            libevdev.evbit(btn_name)
        except Exception:
            logging.warning(f"BUTTON_THRESHOLDS typo or invalid key: '{btn_name}' will be ignored.")
            
    for btn_name in list(BUTTON_MAP.keys()):
        try:
            libevdev.evbit(btn_name)
        except Exception:
            logging.warning(f"BUTTON_MAP typo or invalid key: '{btn_name}' will be ignored.")

    buttons_list = args.buttons if args.buttons else list(FILTERED_BUTTONS)
    axes_list = list(FILTERED_SCROLL_AXES)
    
    buttons_to_filter = []
    for b in buttons_list:
        try:
            if b: buttons_to_filter.append(libevdev.evbit(b))
        except Exception as e:
            logging.warning(f"Button '{b}' ignored: {e}")

    axes_to_filter = []
    for a in axes_list:
        try:
            if a: axes_to_filter.append(libevdev.evbit(a))
        except Exception as e:
            logging.warning(f"Axis '{a}' ignored: {e}")

    if BUTTON_MAP: logging.info(f"Loaded {len(BUTTON_MAP)} Button Mappings: {BUTTON_MAP}")
    if BUTTON_THRESHOLDS: logging.info(f"Loaded {len(BUTTON_THRESHOLDS)} Custom Thresholds: {BUTTON_THRESHOLDS}")

    # CONFIG PRECEDENCE: CLI args > mouse_config.py > Interactive Prompt
    # This prevents Systemd from freezing at boot if it hits an input() prompt!
    if args.mouse:
        device_name_str = args.mouse
    elif DEVICE_NAME:
        device_name_str = DEVICE_NAME
    else:
        logging.warning("No device specified in CLI or config. Falling back to interactive prompt.")
        device_name_str = retrieve_mouse_name()

    device_path = abs_mouse_path(device_name_str)

    if args.reconnect:
        # INFINITE RETRY LOOP (Best for Cron, SysVinit, and Manual Terminal usage)
        while True:
            if not os.path.exists(device_path):
                logging.info(f"Waiting for mouse '{device_name_str}' to connect...")
                time.sleep(2)
                continue

            try:
                with open(device_path, 'rb') as fd:
                    device = libevdev.Device(fd)
                    logging.info(f"Successfully connected to '{device_name_str}'")
                    filter_mouse_chattering(device, args.threshold, args.scroll_reverse, args.scroll_double, 
                                            args.jump_limit, buttons_to_filter, axes_to_filter, 
                                            BUTTON_THRESHOLDS, BUTTON_MAP)
            except OSError as e:
                if e.errno == 19:
                    logging.warning("Mouse disconnected. Waiting for reconnect...")
                else:
                    logging.error(f"OS Error: {e}. Retrying in 2s...")
                time.sleep(2)
            except Exception as e:
                logging.error(f"Unexpected Error: {e}. Retrying in 2s...")
                time.sleep(2)
    else:
        # FAIL & EXIT MODE (Default: Best for Systemd, OpenRC, and Runit)
        if not os.path.exists(device_path):
            logging.critical(f"Mouse '{device_name_str}' not found. Exiting cleanly.")
            sys.exit(0)
            
        try:
            with open(device_path, 'rb') as fd:
                device = libevdev.Device(fd)
                logging.info(f"Successfully connected to '{device_name_str}'")
                filter_mouse_chattering(device, args.threshold, args.scroll_reverse, args.scroll_double, 
                                        args.jump_limit, buttons_to_filter, axes_to_filter, 
                                        BUTTON_THRESHOLDS, BUTTON_MAP)
        except OSError as e:
            if e.errno == 19:
                logging.critical("Mouse disconnected. Exiting cleanly.")
                sys.exit(0)
            else:
                raise e

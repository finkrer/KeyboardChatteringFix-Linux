import argparse
import logging
import sys
import os
import time
import libevdev

from src.keyboard_filtering import filter_chattering
from src.keyboard_retrieval import retrieve_keyboard_name, INPUT_DEVICES_PATH, abs_keyboard_path

# Safely import the config file if it exists
try:
    from src.keyboard_config import DEVICE_NAME, FILTERED_KEYS, KEY_THRESHOLDS, KEY_MAP
except ImportError:
    DEVICE_NAME, FILTERED_KEYS, KEY_THRESHOLDS, KEY_MAP = "", set(), {}, {}

def parse_keys(keys_str):
    """Parses comma-separated CLI arguments into a list of strings."""
    if not keys_str: return []
    return [key.strip() for key in keys_str.split(',')]
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-k', '--keyboard', type=str, default=str())
    parser.add_argument('-t', '--threshold', type=int, default=30)
    parser.add_argument('-r', '--reconnect', action='store_true', help="Loop infinitely and wait for device reconnection instead of exiting")
    parser.add_argument('--keys', type=parse_keys, default=[])
    parser.add_argument('-v', '--verbosity', type=int, default=1, choices=[0, 1, 2])
    args = parser.parse_args()

    logging.basicConfig(level={0: logging.CRITICAL, 1: logging.INFO, 2: logging.DEBUG}[args.verbosity],
                        handlers=[logging.StreamHandler(sys.stdout)],
                        format="%(asctime)s - %(message)s", datefmt="%H:%M:%S")

    # PREVENT SILENT FAILURES: Validate config thresholds/maps at startup
    for key_name in list(KEY_THRESHOLDS.keys()):
        try:
            libevdev.evbit(key_name)
        except Exception:
            logging.warning(f"KEY_THRESHOLDS typo or invalid key: '{key_name}' will be ignored.")
            
    for key_name in list(KEY_MAP.keys()):
        try:
            libevdev.evbit(key_name)
        except Exception:
            logging.warning(f"KEY_MAP typo or invalid key: '{key_name}' will be ignored.")

    keys_list = args.keys if args.keys else list(FILTERED_KEYS)
    keys_to_filter = []
    
    # Convert string key names (e.g., "KEY_A") to libevdev.EventCode objects
    for key in keys_list:
        try:
            if key: keys_to_filter.append(libevdev.evbit(key))
        except Exception as e:
            logging.warning(f"Key '{key}' ignored: {e}")

    if KEY_MAP: logging.info(f"Loaded {len(KEY_MAP)} Key Mappings: {KEY_MAP}")
    if KEY_THRESHOLDS: logging.info(f"Loaded {len(KEY_THRESHOLDS)} Custom Thresholds: {KEY_THRESHOLDS}")

    # CONFIG PRECEDENCE: CLI args > keyboard_config.py > Interactive Prompt
    # This prevents Systemd from freezing at boot if it hits an input() prompt!
    if args.keyboard:
        device_name_str = args.keyboard
    elif DEVICE_NAME:
        device_name_str = DEVICE_NAME
    else:
        logging.warning("No device specified in CLI or config. Falling back to interactive prompt.")
        device_name_str = retrieve_keyboard_name()

    device_path = abs_keyboard_path(device_name_str)

    if args.reconnect:
        # INFINITE RETRY LOOP (Best for Cron, SysVinit, and Manual Terminal usage)
        while True:
            if not os.path.exists(device_path):
                logging.info(f"Waiting for keyboard '{device_name_str}' to connect...")
                time.sleep(2)
                continue

            try:
                with open(device_path, 'rb') as fd:
                    device = libevdev.Device(fd)
                    logging.info(f"Successfully connected to '{device_name_str}'")
                    filter_chattering(device, args.threshold, keys_to_filter, KEY_THRESHOLDS, KEY_MAP)
            except OSError as e:
                if e.errno == 19:
                    logging.warning("Keyboard disconnected. Waiting for reconnect...")
                else:
                    logging.error(f"OS Error: {e}. Retrying in 2s...")
                time.sleep(2)
            except Exception as e:
                logging.error(f"Unexpected Error: {e}. Retrying in 2s...")
                time.sleep(2)
    else:
        # FAIL & EXIT MODE (Default: Best for Systemd, OpenRC, and Runit)
        if not os.path.exists(device_path):
            logging.critical(f"Keyboard '{device_name_str}' not found. Exiting cleanly.")
            sys.exit(0)
            
        try:
            with open(device_path, 'rb') as fd:
                device = libevdev.Device(fd)
                logging.info(f"Successfully connected to '{device_name_str}'")
                filter_chattering(device, args.threshold, keys_to_filter, KEY_THRESHOLDS, KEY_MAP)
        except OSError as e:
            if e.errno == 19:
                logging.critical("Keyboard disconnected. Exiting cleanly.")
                sys.exit(0)
            else:
                raise e

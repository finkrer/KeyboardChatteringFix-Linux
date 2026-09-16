# __Keyboard & Mouse Chattering Fix for Linux__

[![GitHub](https://img.shields.io/github/license/w2sv/KeyboardChatteringFix-Linux?)](LICENSE)

__A tool for filtering mechanical keyboard chattering and mouse double-clicking on Linux__

## The problem

Switches on mechanical keyboards occasionally start to "chatter" or "bounce", meaning when you press a key with a faulty switch it erroneously detects two or even more key presses. Similarly, mechanical switches on mice (especially gaming mice) frequently develop "double-click" issues, and faulty scroll wheel encoders will randomly glitch and scroll in the wrong direction.

## The existing solutions

Apart from buying new hardware, there have been ways to deal with this problem using software methods. The idea is to filter inputs that occur faster than a certain threshold. "Keyboard Chattering Fix v 0.0.1" is a tool I had been using on Windows for a long time, and these days you also have [Keyboard Chatter Blocker](https://github.com/mcmonkeyprojects/KeyboardChatterBlocker). 

Unfortunately, all existing tools only work on Windows. On Linux, the answer everyone seems to give is to use the Bounce Keys feature of X, but it's not really useful in this way. For one, it resets the delay even on filtered key presses, meaning that if you press the key fast enough, *none* of the presses will pass through, ever. 

## This project's solution

This tool attempts to solve these hardware problems by having full low-level access and control over all input events. Using `libevdev`'s Python bindings, it grabs your device and processes its events, then outputs the result back to the system using `/dev/uinput`. This effectively emulates a flawless keyboard and mouse that doesn't chatter or double-click, unlike your real ones!

This also means it works across the whole system, without depending on X11 or Wayland.

*Note for Mice:* To ensure your mouse cursor remains flawlessly smooth, this tool uses completely separate logic for mice. It natively bypasses X/Y cursor movement and scrolling, applying the chatter filter *only* to physical button clicks (Left click, Right click, Side buttons, etc.).

As for the filtering rule, what seems to work well is the time between the last "key up" event and the current "key down" event. When the switch chatters, that time is very low - around 10 ms. By filtering such anomalies, we remove chatter without impeding actual fast typing or clicking.

## Installation

Download the repository and extract the files. `cd` into the extracted folder.

Due to PEP 668 on modern Linux distributions, globally installing Python packages via `pip` is restricted to prevent breaking system tools. You have two options to install the required `libevdev` dependency:

### Option 1: Python Virtual Environment (Recommended)
Using the built-in `venv` module is the safest and cleanest way to run this tool.
```shell
# 1. Create a virtual environment named 'venv' inside the project folder
python3 -m venv venv

# 2. Activate the virtual environment
source venv/bin/activate

# 3. Install the dependencies inside the isolated environment
pip install -r requirements.txt
```

### Option 2: Global Install (Quickest)
If you do not want to use a virtual environment, you can override the system protection flag.
```shell
sudo pip3 install -r requirements.txt --break-system-packages
```

## Usage

Because keyboards and mice are handled differently by the OS, they are executed as separate modules. 

**If you used a Virtual Environment (Option 1):**
Because `sudo` drops your local path, you must point `sudo` directly to your virtual environment's Python binary:
```shell
sudo venv/bin/python3 -m src.keyboard_main
sudo venv/bin/python3 -m src.mouse_main
```

**If you installed Globally (Option 2):**
```shell
sudo python3 -m src.keyboard_main
sudo python3 -m src.mouse_main
```

### Customization Options

- `-k KEYBOARD`, `--keyboard KEYBOARD`
  - Name of your chattering keyboard device as listed in `/dev/input/by-id`. If left unset, it will attempt to retrieve it automatically. 
- `-m MOUSE`, `--mouse MOUSE`
  - Name of your double-clicking mouse device. Works identically to the keyboard argument above.
- `-t THRESHOLD`, `--threshold THRESHOLD`
  - Filter time threshold in milliseconds. Default=30ms. Note: This denotes the time between a key/button being *released* and pressed again. For reference, if you click really fast, this delay is around 50 ms.
- `-r`, `--reconnect`
  - Runs an infinite retry loop to wait for disconnected devices. Use this if running manually in a terminal or using `cron`, but **DO NOT** use this if using Systemd! Systemd natively handles restarts much cleaner in the background.
- `--keys KEYS` (For Keyboard)
  - Comma-separated list of specific keys to filter (e.g., `KEY_A,KEY_SPACE`). If provided, *only* these keys will be filtered, leaving the rest of your keyboard untouched. You can also permanently define these in `src/keyboard_config.py`.
- `--buttons BUTTONS` (For Mouse)
  - Comma-separated list of specific buttons to filter (e.g., `BTN_LEFT,BTN_RIGHT`). You can also permanently define these in `src/mouse_config.py`.

### Advanced Mouse & Sensor Filtering Features
If you have a faulty mouse sensor or a broken scroll wheel, you can pass these additional arguments to `mouse_main`:
- `-sr SCROLL_REV`, `--scroll-reverse SCROLL_REV`
  - Fixes scroll wheels that jump in the opposite direction. Filters direction changes that occur faster than the threshold. Default=0 (Disabled). Try `100` to `150` for glitchy wheels.
- `-sd SCROLL_DBL`, `--scroll-double SCROLL_DBL`
  - Fixes worn encoders firing two ticks for one physical notch. Filters identical scrolls happening too fast. Default=0 (Disabled). *(Caution: Do not use this if your mouse has an infinite free-spinning scroll wheel!)*
- `-jl JUMP`, `--jump-limit JUMP`
  - Blocks massive teleporting cursor jumps caused by dirty laser sensors or hairs. Drops frames exceeding X pixels (e.g., `300`).

### Hotplugging, Remapping & Per-Key Thresholds
The configuration files (`src/keyboard_config.py` and `src/mouse_config.py`) contain powerful advanced options:
- **Per-Key Thresholds:** Keys physically wear differently. You can set your heavy Spacebar to a `50ms` delay to prevent chatter, while leaving your `A` key at `15ms` for fast gaming. 
- **Remapping / Macros:** Because this intercepts kernel events, you can natively remap buttons (e.g. swap `KEY_CAPSLOCK` to `KEY_LEFTCTRL`, or `BTN_SIDE` to `BTN_MIDDLE`). This works flawlessly on both X11 and Wayland.

### Understanding Linux Input Devices (Which one do I pick?)

Modern gaming peripherals (like Corsair, Razer, or Logitech) are "composite USB devices". This means a single physical mouse might tell Linux it is actually a mouse, a keyboard, and a multimedia controller all at once! 

Because of this, both the keyboard and mouse scripts will list *all* available event endpoints to give you maximum flexibility. Here is a guide on which one to choose:

- **`-event-kbd`**: The primary endpoint for standard keystrokes. For keyboards, select this to fix chattering on standard keys (A-Z, 0-9). 
- **`-event-mouse`**: The primary endpoint for standard mouse clicks (Left, Right, Middle) and X/Y movement. Select this to fix standard mouse double-clicking.
- **`-ifXX-event-kbd` (Virtual Keyboards)**: Advanced gaming mice often register a "virtual keyboard" to handle macro side-buttons. If your mouse's side buttons are double-clicking, you may need to point the mouse script at this endpoint instead of the standard mouse endpoint!
- **`-event-ifXX` (Interfaces)**: These handle multimedia controls (Volume wheels, Play/Pause) or vendor-specific data (RGB lighting). You rarely need to select these.

**Troubleshooting Manual Testing:**
If you run the script manually in the terminal and receive a `[Errno 16] Device or resource busy` error, it means you have a background service currently running! The script requires an exclusive lock on the hardware. Stop your background service to release the lock before testing manually.

## Automation (Systemd)

Starting the scripts manually every time is not ideal. You should set them up as background Systemd services. 

### Step 1: Configure the shell scripts
Modify `keyboard_chattering.sh` and/or `mouse_chattering.sh` to `cd` into the absolute path of your downloaded folder, and input your device IDs and desired thresholds. *(Note: If using a venv, replace `python3` with `venv/bin/python3`).*

**Example `keyboard_chattering.sh`:**
```shell
cd /home/foouser/Downloads/HardwareChatteringFix-Linux/ && sudo python3 -m src.keyboard_main -k usb-Logitech_Keyboard-event-kbd -t 40 --keys KEY_E,KEY_SPACE
```

**Example `mouse_chattering.sh`:**
```shell
cd /home/foouser/Downloads/HardwareChatteringFix-Linux/ && sudo python3 -m src.mouse_main -m usb-Logitech_Mouse-event-mouse -t 50 --buttons BTN_LEFT,BTN_RIGHT
```

Make sure to change the file permissions so they are executable:
```shell
chmod +x keyboard_chattering.sh mouse_chattering.sh
```

### Step 2: Configure the service files
Edit `keyboard_chattering.service` and `mouse_chattering.service` to point `ExecStart` to the absolute path of your `.sh` files. 

**Example keyboard_chattering.service:**
```shell
ExecStart=/home/foouser/Downloads/HardwareChatteringFix-Linux/keyboard_chattering.sh
```

**Example mouse_chattering.service:**
```shell
ExecStart=/home/foouser/Downloads/HardwareChatteringFix-Linux/mouse_chattering.sh
```

### Step 3: Enable the Services (Separately or Combined)

Copy the `.service` files to your systemd folder:
```shell
sudo cp keyboard_chattering.service /etc/systemd/system/
sudo cp mouse_chattering.service /etc/systemd/system/
```

**To enable ONLY the keyboard fix:**
```shell
sudo systemctl enable --now keyboard_chattering
```

**To enable ONLY the mouse fix:**
```shell
sudo systemctl enable --now mouse_chattering
```

**To run BOTH concurrently:**
Simply run both enable commands! They operate completely independently of one another.
```shell
sudo systemctl enable --now keyboard_chattering
sudo systemctl enable --now mouse_chattering
```

### Step 4: Checking Status and Logs

You can check if the scripts are running properly by checking their independent statuses:

**For the Keyboard:**
```shell
systemctl status keyboard_chattering.service
journalctl -xeu keyboard_chattering.service
```

**For the Mouse:**
```shell
systemctl status mouse_chattering.service
journalctl -xeu mouse_chattering.service
```

### Step 5: Applying Changes

How you apply changes depends on which files you modified. 

**Scenario A: You edited the Python code, `config.py`, or the `.sh` shell scripts**

Systemd doesn't need to reload its own configuration; it just needs to restart the service to execute the newly saved scripts.
```shell
# For the Keyboard:
sudo systemctl restart keyboard_chattering.service

# For the Mouse:
sudo systemctl restart mouse_chattering.service
```

**Scenario B: You edited the `.service` files themselves**

If you changed settings inside the `.service` files (like `Restart=`, `ExecStart=`, etc.), you must tell systemd to re-read those files from disk before restarting.
```shell
# For the Keyboard:
sudo systemctl stop keyboard_chattering.service      # Safely stops the current running instance
sudo systemctl daemon-reload                         # Tells systemd to read the updated .service file
sudo systemctl restart keyboard_chattering.service   # Starts the service using the new configuration

# For the Mouse:
sudo systemctl stop mouse_chattering.service
sudo systemctl daemon-reload
sudo systemctl restart mouse_chattering.service
```

**Scenario C: You edited the `[Install]` section of the `.service` files**

The `[Install]` section dictates *when* and *how* the service starts at boot (via `WantedBy=`). If you changed this section, you must re-enable the service to update the boot symlinks.
```shell
# For the Keyboard:
sudo systemctl stop keyboard_chattering.service
sudo systemctl daemon-reload
sudo systemctl reenable keyboard_chattering.service  # Removes old boot symlinks and creates new ones
sudo systemctl restart keyboard_chattering.service

# For the Mouse:
sudo systemctl stop mouse_chattering.service
sudo systemctl daemon-reload
sudo systemctl reenable mouse_chattering.service
sudo systemctl restart mouse_chattering.service
```

---

## Automation (Non-Systemd & BSD)

Because the Python scripts rely natively on the OS Kernel (`evdev` and `uinput`), the code works perfectly on non-systemd distributions and BSD variants. Ensure your `.sh` scripts are configured and executable (`chmod +x`), then use the guide below for your specific init system.

**IMPORTANT SUSPEND/SLEEP WARNING:**
Systemd natively restarts scripts when a PC wakes from sleep. Non-systemd init systems **do not**. Therefore, if you use *any* of the methods below, you **MUST** append the `-r` (Auto-Reconnect) flag to the execution line inside your `.sh` scripts!
```bash
# Example: The -r flag ensures the script survives sleep/suspend cycles!
cd /path/to/folder && sudo python3 -m src.keyboard_main -k <ID> -t 30 -r
```

> **💡 PRO-TIP FOR LOGGING:** Since non-systemd systems lack `journalctl`, you should modify your `.sh` scripts to redirect output so you can read the logs. Append a redirect to the execution lines in your `.sh` files:
> ```bash
> # For the keyboard script:
> cd /absolute/path/to/project && sudo python3 -m src.keyboard_main -k <KEYBOARD id> -t 30 >> /var/log/keyboard_fix.log 2>&1
> 
> # For the mouse script:
> cd /absolute/path/to/project && sudo python3 -m src.mouse_main -m <MOUSE id> -t 30 >> /var/log/mouse_fix.log 2>&1
> ```
> You can then read your logs anytime using `cat /var/log/keyboard_fix.log` or `cat /var/log/mouse_fix.log`.

---

### Cron (Universal Fallback)

Cron does not restart scripts natively. You **MUST** add the `-r` flag to your `.sh` scripts.

The easiest way to run the scripts on any system without Systemd is using `cron`'s `@reboot` directive.

1. Because `cron` does not auto-restart failed scripts, you **MUST** add the `-r` flag to your `.sh` scripts so they survive hardware disconnects!
   ```bash
   # Example addition inside your .sh files:
   python3 -m src.keyboard_main -k <ID> -t 30 -r
   python3 -m src.mouse_main -m <ID> -t 30 -r
   ```
2. Open the root crontab: `sudo crontab -e`
3. Add both scripts to run in the background (using `&`):
   ```text
   @reboot /absolute/path/to/keyboard_chattering.sh &
   @reboot /absolute/path/to/mouse_chattering.sh &
   ```

**Operational Commands:**
* **Start Right Now:** 
  ```bash
  sudo /absolute/path/to/keyboard_chattering.sh &
  sudo /absolute/path/to/mouse_chattering.sh &
  ```
* **Stop:** 
  ```bash
  sudo pkill -f keyboard_main
  sudo pkill -f mouse_main
  ```
* **Status/Logs:** 
  ```bash
  ps aux | grep -E 'keyboard_main|mouse_main'
  cat /var/log/keyboard_fix.log
  cat /var/log/mouse_fix.log
  ```
* **Restart:** 
  ```bash
  sudo pkill -f keyboard_main; sudo /absolute/path/to/keyboard_chattering.sh &
  sudo pkill -f mouse_main; sudo /absolute/path/to/mouse_chattering.sh &
  ```
* **Reenable (Boot Integration):** Run `sudo crontab -e` and update the `@reboot` lines. Cron applies changes automatically on next boot.

---

### OpenRC (Artix, Alpine, Gentoo)

Even though OpenRC supports native respawning, you **MUST** add the `-r` flag to your `.sh` scripts. This prevents the script from crash-looping when the USB bus briefly drops during sleep/wake cycles.

1. Create two files: `sudo nano /etc/init.d/keyboard_fix` and `sudo nano /etc/init.d/mouse_fix`
2. Paste the appropriate template below into each file:

**Keyboard Template (`/etc/init.d/keyboard_fix`):**
```bash
#!/sbin/openrc-run
name="Keyboard Chattering Fix"
command="/absolute/path/to/keyboard_chattering.sh"
command_background=true
pidfile="/run/keyboard_fix.pid"

# Enable native systemd-like auto-restarts!
respawn=true
respawn_delay=5

depend() { need localmount }
```

**Mouse Template (`/etc/init.d/mouse_fix`):**
```bash
#!/sbin/openrc-run
name="Mouse Chattering Fix"
command="/absolute/path/to/mouse_chattering.sh"
command_background=true
pidfile="/run/mouse_fix.pid"

respawn=true
respawn_delay=5

depend() { need localmount }
```

3. Make them executable: `sudo chmod +x /etc/init.d/keyboard_fix /etc/init.d/mouse_fix`
4. Enable at boot: 
   ```bash
   sudo rc-update add keyboard_fix default
   sudo rc-update add mouse_fix default
   ```

**Operational Commands:**
* **Start Right Now:** 
  ```bash
  sudo rc-service keyboard_fix start
  sudo rc-service mouse_fix start
  ```
* **Stop:** 
  ```bash
  sudo rc-service keyboard_fix stop
  sudo rc-service mouse_fix stop
  ```
* **Status/Logs:** 
  ```bash
  sudo rc-service keyboard_fix status
  sudo rc-service mouse_fix status
  cat /var/log/keyboard_fix.log
  cat /var/log/mouse_fix.log
  ```
* **Restart:** 
  ```bash
  sudo rc-service keyboard_fix restart
  sudo rc-service mouse_fix restart
  ```
* **Reenable (Boot Integration):** 
  ```bash
  sudo rc-update del keyboard_fix default && sudo rc-update add keyboard_fix default
  sudo rc-update del mouse_fix default && sudo rc-update add mouse_fix default
  ```

---

### Runit (Void Linux)

Even though Runit supports native respawning, you **MUST** add the `-r` flag to your `.sh` scripts. This prevents the script from crash-looping when the USB bus briefly drops during sleep/wake cycles.

1. Create service directories: 
   ```bash
   sudo mkdir -p /etc/sv/keyboard_fix /etc/sv/mouse_fix
   ```
2. Create a run file for the keyboard: `sudo nano /etc/sv/keyboard_fix/run`
   ```bash
   #!/bin/sh
   exec /absolute/path/to/keyboard_chattering.sh
   ```
3. Create a run file for the mouse: `sudo nano /etc/sv/mouse_fix/run`
   ```bash
   #!/bin/sh
   exec /absolute/path/to/mouse_chattering.sh
   ```
4. Make both executable: 
   ```bash
   sudo chmod +x /etc/sv/keyboard_fix/run /etc/sv/mouse_fix/run
   ```
5. Enable them (symlink to runit's service directory): 
   ```bash
   sudo ln -s /etc/sv/keyboard_fix /var/service/
   sudo ln -s /etc/sv/mouse_fix /var/service/
   ```

**Operational Commands:**
* **Start Right Now:** Runit detects the symlinks and starts them automatically!
* **Stop:** 
  ```bash
  sudo sv stop keyboard_fix
  sudo sv stop mouse_fix
  ```
* **Status/Logs:** 
  ```bash
  sudo sv status keyboard_fix mouse_fix
  cat /var/log/keyboard_fix.log
  cat /var/log/mouse_fix.log
  ```
* **Restart:** 
  ```bash
  sudo sv restart keyboard_fix
  sudo sv restart mouse_fix
  ```
* **Reenable (Boot Integration):** 
  ```bash
  sudo rm /var/service/keyboard_fix && sudo ln -s /etc/sv/keyboard_fix /var/service/
  sudo rm /var/service/mouse_fix && sudo ln -s /etc/sv/mouse_fix /var/service/
  ```

---

### SysVinit (Devuan, Older Distros)

SysVinit does not restart scripts natively. You **MUST** add the `-r` flag to your `.sh` scripts.

Simply add the executable scripts to your `/etc/rc.local` file before the `exit 0` line:
```bash
/absolute/path/to/keyboard_chattering.sh &
/absolute/path/to/mouse_chattering.sh &
exit 0
```

**Operational Commands:**
* **Start Right Now:** 
  ```bash
  sudo /etc/rc.local
  ```
* **Stop:** 
  ```bash
  sudo pkill -f keyboard_main
  sudo pkill -f mouse_main
  ```
* **Status/Logs:** 
  ```bash
  ps aux | grep -E 'keyboard_main|mouse_main'
  cat /var/log/keyboard_fix.log
  cat /var/log/mouse_fix.log
  ```
* **Restart:** 
  ```bash
  sudo pkill -f keyboard_main; sudo /absolute/path/to/keyboard_chattering.sh &
  sudo pkill -f mouse_main; sudo /absolute/path/to/mouse_chattering.sh &
  ```
* **Reenable (Boot Integration):** *(If using `update-rc.d` instead of `rc.local`)*
  ```bash
  sudo update-rc.d -f keyboard_fix remove && sudo update-rc.d keyboard_fix defaults
  sudo update-rc.d -f mouse_fix remove && sudo update-rc.d mouse_fix defaults
  ```

---

### FreeBSD / BSD Family

FreeBSD does not restart scripts natively. You **MUST** add the `-r` flag to your `.sh` scripts.

FreeBSD has native support for `evdev`, but you must load the modules and adjust device paths.

**1. Load evdev modules:** Add these to `/boot/loader.conf` and reboot (or `kldload` them now):
```text
evdev_load="YES"
uinput_load="YES"
```

**2. Find your Device Path:** 
FreeBSD does not use Linux's `udev` naming conventions. The folder `/dev/input/by-id/` does not exist on BSD! Instead, FreeBSD lists devices as raw event nodes (`/dev/input/event0`, `event1`, etc.).
Update your `.sh` scripts to pass the raw absolute path directly to `-k` or `-m` (which overrides the auto-search scripts):
```bash
# Example keyboard_chattering.sh
cd /path/to/folder && sudo python3 -m src.keyboard_main -k /dev/input/event0 -t 30 >> /var/log/keyboard_fix.log 2>&1

# Example mouse_chattering.sh
cd /path/to/folder && sudo python3 -m src.mouse_main -m /dev/input/event1 -t 30 >> /var/log/mouse_fix.log 2>&1
```

**3. Automate using `rc.d` scripts:**
Create two files: `sudo nano /usr/local/etc/rc.d/keyboard_fix` and `sudo nano /usr/local/etc/rc.d/mouse_fix`.

**Keyboard Template (`/usr/local/etc/rc.d/keyboard_fix`):**
```bash
#!/bin/sh
# REQUIRE: DAEMON
# PROVIDE: keyboard_fix

. /etc/rc.subr

name="keyboard_fix"
rcvar="keyboard_fix_enable"

# Use daemon to securely background the script.
# We pass the -r flag to 'daemon' so it auto-restarts the script if it dies!
command="/usr/sbin/daemon"
command_args="-r -P /var/run/keyboard_fix.pid -f /absolute/path/to/keyboard_chattering.sh"

load_rc_config $name
run_rc_command "$1"
```

**Mouse Template (`/usr/local/etc/rc.d/mouse_fix`):**
```bash
#!/bin/sh
# REQUIRE: DAEMON
# PROVIDE: mouse_fix

. /etc/rc.subr

name="mouse_fix"
rcvar="mouse_fix_enable"

command="/usr/sbin/daemon"
command_args="-r -P /var/run/mouse_fix.pid -f /absolute/path/to/mouse_chattering.sh"

load_rc_config $name
run_rc_command "$1"
```

4. Make them executable: `sudo chmod +x /usr/local/etc/rc.d/keyboard_fix /usr/local/etc/rc.d/mouse_fix`
5. Enable them in your `/etc/rc.conf`:
   ```text
   keyboard_fix_enable="YES"
   mouse_fix_enable="YES"
   ```

**Operational Commands:**
* **Start Right Now:** 
  ```bash
  sudo service keyboard_fix start
  sudo service mouse_fix start
  ```
* **Stop:** 
  ```bash
  sudo service keyboard_fix stop
  sudo service mouse_fix stop
  ```
* **Status/Logs:** 
  ```bash
  sudo service keyboard_fix status
  sudo service mouse_fix status
  cat /var/log/keyboard_fix.log
  cat /var/log/mouse_fix.log
  ```
* **Restart:** 
  ```bash
  sudo service keyboard_fix restart
  sudo service mouse_fix restart
  ```
* **Reenable (Boot Integration):** Ensure `/etc/rc.conf` contains the enable variables. You can quickly force them using:
  ```bash
  sudo sysrc keyboard_fix_enable="YES"
  sudo sysrc mouse_fix_enable="YES"
  ```

# Keyboard Chattering Fix for Linux

This is a tool for blocking mechanical keyboard chattering on Linux.

---

## The problem

Switches on mechanical keyboards occasionally start to "chatter",
meaning when you press a key with a faulty switch it actually detects
as two or even more keypresses in rapid succession.

## The existing solutions

Apart from buying a new keyboard, there have been ways to deal
with this problems using software methods. The idea is to filter keypresses
that occur faster than a certain threshold. "Keyboard Chattering Fix v 0.0.1"
is a tool I had been using on Windows for a long time, and these days you also have
[Keyboard Chatter Blocker](https://github.com/mcmonkeyprojects/KeyboardChatterBlocker),
which is a nice open source tool with some additional functionality. It's actually what
I use myself when I use Windows.

Unfortunately, all existing tools only work on Windows.
On Linux, the answer everyone seems to give is to use the Bounce Keys feature of X,
but it's not really useful in this way. For one, it resets the delay even on filtered
keypresses, meaning that if you press the key fast enough,
*none* of the presses with pass through, ever. And if the key chatters,
this is bound to happen eventually and interfere with fast repeated keypresses.

## This project's solution

This tool attempts to solve any such problems that may arise by having full low-level access
and control over all keyboard events.
Using `libevdev`'s Python bindings, it grabs your keyboard's event device and processes its events,
then outputs the result back to the system using `/dev/uinput`, effectively emulating a keyboard -
one that doesn't chatter, unlike your real one!

This also means it works across the system, without depending on X.

As for the filtering rule, what seems to work well is the time between the last key up event
and the current key down event. When the key chatters, that time seems to be very low - around 10 ms.
By filtering such anomalies, we can hopefully remove chatter without impeding actual fast keypresses.

## Installation

Just get the Python script by cloning the repository, or download it directly.

Of course, you will also need `libevdev` and the Python bindings installed.
Both can most likely be found in your distribution's repositories.

If your distribution offers a version of Python that's not exactly recent,
it might take issue with some of the fancy new language features I'm using.
So keep that in mind if you have any issues running the script.

## Usage

```
# chattering_fix.py /dev/input/by-id/usb-I_One_Gaming_keyboard-event-kbd 30
```

Note the need for superuser privileges.

The first argument is the keyboard device we need to take over.
I use `by-id` here since those ids are persistent, unlike the event device numbers.
The ids should be clear enough that it's not hard to find the one you need in that directory.

The second argument is the filter threshold in milliseconds.
This is not between keypresses, but between a key being released and pressed again,
so the number should probably be lower than you might be used to.
For reference, if you press the key really fast this delay is around 50 ms.

## Automation

Starting the script manually every time doesn't sound like the greatest idea, so
you should probably consider something that does it for you. The solution I provide
is a systemd unit file. Copy it to `/etc/systemd/system/`, then enable it with
`systemctl enable --now chattering_fix`. Don't forget to change the command inside to
tell the service what id your keyboard has and where the script is located.

## Future plans

For now I'm just hoping this works and my keyboard doesn't chatter.

If this is of use to you and you have any suggestions or bug reports feel free to tell me.

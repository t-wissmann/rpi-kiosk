# rpi-kiosk

The scripts and the documentation in this repository turn your Raspberry Pi (in
my case '4 Model B') into a kiosk screen.

If you don't already have a runing raspberry pi yet, then see
[SYSTEM-SETUP.md](SYSTEM-SETUP.md) for some basic installation notes. If you
already have a running system, just continue here.

## X vs Wayland

The current scripts use X11 (which should be raspian default), but you can switch to X11 via `sudo raspi-config`.

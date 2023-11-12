# rpi-kiosk - System Setup

This file describes how I set up the raspberry pi to be in a rather minimal
configuration. So in particular, it lists what I uninstalled. If you already
have a running rpi instance your happy with, then you don't need this file.


## Create an SD-Card image

I've installed the [rpi-imager](https://github.com/raspberrypi/rpi-imager) on
my computer, to fill the sd card. There aren't many options. Just do anything
to get a bootable image, don't bother too much. In my case, the wifi-password
that I entered in the rpi-image didn't make the raspberry pi connect to the
wifi anyway (maybe I made a typo?). Hence, just create a bootable image and
have a keyboard and mouse at hand to enter the wifi password directly on your
first boot.

## First Steps

When turning the rpi on for the first time, the system booted directly to
desktop (i.e. autologin).

## Updating the system

Keep the packages up to date all the time! Run:
```bash
sudo apt-get updage
sudo apt-get upgrade
```
in order to install new packages. Sometimes, some packages have been kept back
for the first update phase. If so, it might be necessary to also run this
afterwards:
```bash
sudo apt-get --with-new-pkgs upgrade
```
Afterwards, give the system a reboot (`systemctl reboot -i`).

## Recommended Packages
```bash
sudo apt-get install pavucontrol xterm vim
```
## Non-Recommended Software
To minimize the attack surface, I recommend removing or disabling the following
software, if not needed:

  - bluetooth:
  ```
  sudo systemctl disable bluetooth
  ```
  - printing:
  ```
  sudo systemctl disable cups
  ```
  - disable splash screen:
    ```
    sudo raspi-config
    ```
    and then System Options → S6 Splash Screen
    (manually: remove the `splash` from `/boot/cmdline.txt`)

## Recommended Settings

```
wget https://github.com/t-wissmann/dotfiles/raw/master/tmux.conf -O ~/.tmux.conf
```

## Checking network status:
```bash
nmcli
```

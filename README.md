# rpi-kiosk

The scripts and the documentation in this repository turn your Raspberry Pi (in
my case '4 Model B') into a kiosk screen.

If you don't already have a runing raspberry pi yet, then see
[SYSTEM-SETUP.md](SYSTEM-SETUP.md) for some basic installation notes. If you
already have a running system, just continue here.

## Required Software

```
sudo apt-get install tmux xdotool x11-utils wget
sudo apt-get install herbstluftwm picom
sudo apt-get install mpv katarakt
sudo apt-get install feh
```
**TODO:** image and html

<!-- old attempt:
sudo apt-get install compiz-{core,plugins,plugins-extra} compizconfig-settings-manager python3-compizconfig
-->

## Setup

### X11

The current scripts require X11 and that the rpi automatically boots in the a
user's X11 session:

* switch to X11 via `sudo raspi-config`
* configure auto-login with Desktop (also in `sudo raspi-config`)
* set the session type to `herbstluftwm` in `/etc/lightdm/lightdm.conf` by setting `autologin-session`:
```
autologin-session=herbstluftwm
```

### Configure Window Manager

Run:
```
mkdir -p ~/.config
ln -svrf herbstluftwm ~/.config/
ln -svrf katarakt.ini ~/.config/
```


### Restart the X11 session:
```
sudo systemctl restart lightdm
```


### Reverse SSH Portforward
Create a user `portforward` and a file `/etc/systemd/system/ssh-portforward.service` containing
```ini
[Unit]
Description=Reverse SSH connection
After=network.target

[Service]
Type=simple
User=portforward
ExecStart=/usr/bin/ssh -v -g -N -T -o "ServerAliveInterval 10" -o "ExitOnForwardFailure yes" -R 10022:localhost:22 portforward@some-public-server.org
Restart=always
RestartSec=5s

[Install]
WantedBy=default.target
```
The `portforward` user needs to be able to connect to the specified server via ssh where preferably [only port forwarding is allowed](https://askubuntu.com/a/50000/547950).

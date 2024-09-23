# rpi-kiosk

The scripts and the documentation in this repository turn your Raspberry Pi (in
my case '4 Model B') into a kiosk screen.

If you don't already have a runing raspberry pi yet, then see
[SYSTEM-SETUP.md](SYSTEM-SETUP.md) for some basic installation notes. If you
already have a running system, just continue here.

## Required Software

```
sudo apt-get install tmux wget
sudo apt-get install mpv katarakt
```
Also, this script requires `wayfire` in version 0.8.1
**TODO:** image and html

## Setup

### Configure window manager

Run:
```
mkdir -p ~/.config
ln -svrf wayfire.ini ~/.config/
ln -svrf katarakt.ini ~/.config/
```
### Configure the desktop session type
Configure `/etc/lightdm/lightdm.conf` such that:
```ini
[Seat:*]
autologin-user=YourUserName
autologin-session=wayfire
user-session=wayfire
```

### Restart the session:
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

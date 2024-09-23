
For historical purposes only, this subdirectory contains old configuration files
for the setup using the x11 window manager [herbstluftwm](https://herbstluftwm.org).
Installation via:
```bash
sudo apt-get install herbstluftwm picom xdotool x11-utils
sudo apt-get install feh
```

<!-- old attempt:
sudo apt-get install compiz-{core,plugins,plugins-extra} compizconfig-settings-manager python3-compizconfig
-->

The current scripts require X11 and that the rpi automatically boots in the a
user's X11 session:

* switch to X11 via `sudo raspi-config`
* configure auto-login with Desktop (also in `sudo raspi-config`)
* set the session type to `herbstluftwm` in `/etc/lightdm/lightdm.conf` by setting `autologin-session`:

```
autologin-session=herbstluftwm
```


### User config files:

Run:
```
mkdir -p ~/.config
ln -svrf herbstluftwm ~/.config/
ln -svrf katarakt.ini ~/.config/
```


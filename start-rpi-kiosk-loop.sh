#!/usr/bin/env bash
#

DIR=$(basename "$0")
$DIR/rpi-kiosk-loop.py --redirect-output=$HOME/logs/rpi-kiosk-loop.log run

if ! [[ "$?" -eq 0 ]] ; then
    sleep 5
    # force screen back on:
    ./tvpower.py --no-send-playback-signal --on
    # and then restart wayland session
    sudo systemctl restart lightdm
fi

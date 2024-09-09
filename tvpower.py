#!/usr/bin/env python3
import sys
import argparse
import subprocess

def main():
    """
    Switch the connected TV screens on and off. Requires
    screens connected via hdmi that can be controlled via cec (using cec-ctl).
    """
    parser = argparse.ArgumentParser(description=main.__help__)
    parser.add_argument('--on', default=False, action='store_true',
                        help='switch hdmi tv screen on')
    parser.add_argument('--off', default=False, action='store_true',
                        help='switch hdmi tv screen off')
    args = parser.parse_args()
    # Some relevant commands:
    # cec-ctl -d0 -t0 --standby
    # cec-ctl -d0 --tv -S
    # cec-ctl -d0 -t0 --active-source phys-addr=2.0.0.0
    # cec-ctl -d0 -t0 --standby
    # cec-ctl -d0 -t0 --image-view-on
    # cec-ctl -d0 -t0 --standby
    # cec-ctl -d0 --tv -S  # <- configure the adapter
    cec_ctl = ['cec-ctl', '-d0']
    if args.on:
        subprocess.run(cec_ctl + ['-t0', '--image-view-on'])
    if args.off:
        subprocess.run(cec_ctl + ['--tv', '-S'])
        subprocess.run(cec_ctl + ['-t0', '--standby'])

if __name__ == "__main__":
    sys.exit(main())

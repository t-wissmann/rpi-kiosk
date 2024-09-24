#!/usr/bin/env python3
import sys
import argparse
import subprocess
import os
import signal


def debug(mesg):
    print(mesg, file=sys.stderr)


def run_cmd(command):
    debug(':: ' + ' '.join(command))
    subprocess.run(command)


def main():
    """
    Switch the connected TV screens on and off. Requires
    screens connected via hdmi that can be controlled via cec (using cec-ctl).
    """
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument('--no-send-playback-signal', dest='send_signal', default=True, action='store_false',
                        help='do not send USR1/USR2 to the rpi kiosk loop for pausing/resuming playback')
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
    rpi_kiosk_loop_pid = None
    if args.send_signal:
        try:
            with open('/tmp/rpi-kiosk.pid') as fh:
                rpi_kiosk_loop_pid = int(fh.read())
            debug(f'rpi-kiosk-loop.py has pid {rpi_kiosk_loop_pid}')
        except Exception as e:
            debug(f'Cannot determine PID of {rpi_kiosk_loop_pid} ({e})')
    cec_ctl = ['cec-ctl', '-d0']
    if args.on:
        run_cmd(cec_ctl + ['--tv', '-S'])
        run_cmd(cec_ctl + ['-t0', '--image-view-on'])
        if rpi_kiosk_loop_pid:
            os.kill(rpi_kiosk_loop_pid, signal.SIGUSR2)
    if args.off:
        run_cmd(cec_ctl + ['--tv', '-S'])
        run_cmd(cec_ctl + ['-t0', '--standby'])
        if rpi_kiosk_loop_pid:
            os.kill(rpi_kiosk_loop_pid, signal.SIGUSR1)
    if not args.on and not args.off:
        debug('Warning: neither --off nor --on supplied.')


if __name__ == "__main__":
    sys.exit(main())

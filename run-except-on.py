#!/usr/bin/env python3
import argparse
import os
import sys
import subprocess
from datetime import datetime
from datetime import date


def parse_date(datestring):
    date_formats = [
        '%Y-%m-%d',
        '%d. %m. %Y',
        '%d.%m.%Y',
    ]
    errors = []
    for f in date_formats:
        try:
            return datetime.strptime(datestring, f).date()
        except ValueError as e:
            errors.append(str(e))
    raise Exception(f'Cannot parse "{datestring}" with any of the formats {date_formats} ({errors})')

def parse_date_file(file_handle):
    entries = []
    for l in file_handle.readlines():
        # strip comments:
        l = l.split('#', 1)[0].strip()
        if l == '':
            continue
        entries.append(parse_date(l))
    return entries


def main():
    """
    Run a given command unless today is a day listed
    as a holiday
    """
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument('--holidays',
                        help='File containing holidays')
    parser.add_argument('COMMAND', nargs='+',
                        help='The command')
    args = parser.parse_args()

    holidays = []
    if args.holidays:
        with open(args.holidays) as fh:
            holidays += parse_date_file(fh)
    if date.today() in holidays:
        # do not do anything
        pass
    else:
        subprocess.run(args.COMMAND)


main()

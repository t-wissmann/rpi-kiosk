#!/usr/bin/env python3
import os
import sys
import argparse
import configparser
import textwrap
import subprocess
import zipfile
from pathlib import Path


def fail(msg):
    raise Exception(msg)


def debug(msg, level=0):
    colors = ['\u001b[0;33m', '\u001b[0;37m']
    level = min(level, len(colors) - 1)
    print('\u001b[0;34m:: ' + colors[level] + str(msg) + '\u001b[0m', file=sys.stderr)


def call_cmd(cmd):
    debug(' '.join(cmd))
    subprocess.run(cmd, check=True)


class State:
    """
    The global state...
    """
    def __init__(self, args):
        self.args = args
        self._config = None

    def config(self):
        if self._config is None:
            # load config if not done yet:
            debug(f"Loading config {self.args.config}")
            self._config = configparser.ConfigParser()
            for sec, entries in self.default_config().items():
                if sec not in self._config.sections():
                    self._config[sec] = {}
                for key, value in entries.items():
                    self._config[sec][key] = value
            self._config.read(self.args.config)
            
        return self._config

    def cfgdir(self, key, section='kiosk'):
        cfg = self.config()
        return os.path.expanduser(cfg[section][key])

    def default_config(self):
        return {
            'kiosk': {
                'cache': '~/.rpi-kiosk/cache/',
                'page-directory': '~/.rpi-kiosk/pages',
            }
        }


def mkdir_force(path):
    """create a directory; ignore if it already exists"""
    try:
        os.makedirs(path)
    except FileExistsError:
        pass


def download(state):
    """
    Download the archive
    """
    cfg = state.config()
    archiveurl = cfg['kiosk']['archiveurl']
    cache = state.cfgdir('cache')
    mkdir_force(cache)
    debug(f"Downloading {archiveurl} to {cache}")
    zippath = os.path.join('archive-current.zip')
    call_cmd(['wget', archiveurl, '-O', zippath])
    page_dir = state.cfgdir('page-directory')
    mkdir_force(page_dir)
    new_files = set()

    with zipfile.ZipFile(zippath) as zipfh:
        for f in zipfh.infolist():
            targetpath = zipfh.extract(f, path=page_dir)
            debug('extracted: ' + targetpath, level=1)
            new_files.add(targetpath)

    debug(f'Removing old files from {page_dir}')
    for dirpath, dirs, files in os.walk(page_dir):
        #print(f'{dirpath} --- {dirs} --- {files}')
        rmcount = 0
        for f in files:
            fp = os.path.join(dirpath, f)  # filepath
            if fp not in new_files:
                debug(f'- rm old file: {fp}', level=1)
                os.remove(fp)
                rmcount += 1
        # remove empty directories:
        if len(dirs) + len(files) == rmcount:
            debug(f'- rm empty dir: {dirpath}', level=1)
            os.rmdir(dirpath)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default=os.path.join(Path.home(), '.config', 'rpi-kiosk.ini'),
                        help='Configuration file; default: ~/.config/rpi-kiosk.ini')
    subcommands = {
        'download': download,
    }
    subparsers = parser.add_subparsers(title='subcommands')
    parser.set_defaults(func=None)

    for cmdname, callback in subcommands.items():
        sp = subparsers.add_parser(cmdname, help=callback.__doc__)
        sp.set_defaults(func=download)

    args = parser.parse_args()
    state = State(args)

    # call subcommand:
    if args.func is not None:
        args.func(state)


main()

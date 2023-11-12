#!/usr/bin/env python3
import os
import sys
import argparse
import configparser
import select
import signal
import time
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
    zippath = os.path.join(cache, 'archive-current.zip')
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


class Page:
    def __init__(self, global_state, index, filepath):
        self.state = global_state
        self.index = index
        self.filepath = filepath
        self.workspace = str(index + 1)
        self.cmd = None
        self.proc = None

    def show_pdf(self):
        debug(f"On {self.workspace}: PDF {self.filepath}")
        self.cmd = [
             '/usr/share/doc/herbstluftwm/examples/exec_on_tag.sh',
             self.workspace,
             'katarakt',
             self.filepath
             ]
        self.proc = subprocess.Popen(self.cmd)

    def detect_type(self):
        pass


def run_posters_signal_handler(signum, frame):
    run_posters.signal_received = signum


def run_posters(state):
    run_posters.signal_received = None
    srcdir = state.cfgdir('page-directory')
    filenames = os.listdir(srcdir)
    pages = []
    signal.signal(signal.SIGINT, run_posters_signal_handler)
    signal.signal(signal.SIGTERM, run_posters_signal_handler)

    for idx, p in enumerate(filenames):
        p = Page(state, idx, os.path.join(srcdir, p))
        pages.append(p)
        p.detect_type()
        p.show_pdf()

    keep_running = True
    while keep_running:
        data_ready = select.select([], [], [], 1.0)[0]
        if run_posters.signal_received is not None:
            debug(f"Exiting because of signal {run_posters.signal_received}")
            keep_running = False
            break

    # send termination signal to all:
    for p in pages:
        p.proc.terminate()

    # wait for them to actually shut down:
    now = time.clock_gettime(time.CLOCK_MONOTONIC)
    # since all have received SIGTERM already, all processes
    # share the timeout:
    total_timeout = now + 20
    try:
        for p in pages:
            p.proc.wait(timeout=max(0, total_timeout - now))
            # update current timestamp:
            now = time.clock_gettime(time.CLOCK_MONOTONIC)
    except TimeoutExpired:
        for p in pages:
            p.proc.kill()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default=os.path.join(Path.home(), '.config', 'rpi-kiosk.ini'),
                        help='Configuration file; default: ~/.config/rpi-kiosk.ini')
    subcommands = {
        'download': download,
        'run': run_posters,
    }
    subparsers = parser.add_subparsers(metavar='SUBCOMMAND', dest='subparser_name')

    for cmdname, callback in subcommands.items():
        sp = subparsers.add_parser(cmdname, help=callback.__doc__)

    args = parser.parse_args()
    state = State(args)

    # call subcommand:
    if args.subparser_name is not None and args.subparser_name in subcommands:
        subcommands[args.subparser_name](state)


main()

#!/usr/bin/env python3
import os
import sys
import argparse
import configparser
import select
import shlex
import signal
import re
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

    def auto_page_switch(self):
        """returns the time between automatic page switches in seconds"""
        if self.args.auto_page_switch is not None:
            return float(self.args.auto_page_switch)
        return float(self.cfgdir('auto-page-switch'))

    def default_config(self):
        return {
            'kiosk': {
                'cache': '~/.rpi-kiosk/cache/',
                'page-directory': '~/.rpi-kiosk/pages',
                'auto-page-switch': '5',
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
        self.runner = None  # the function that runs the viewing programme

    def show_pdf(self):
        self.cmd = [
             '/usr/share/doc/herbstluftwm/examples/exec_on_tag.sh',
             self.workspace,
             'katarakt',
             self.filepath
             ]
        self.proc = subprocess.Popen(self.cmd)

    def show_mpv(self):
        self.cmd = [
             '/usr/share/doc/herbstluftwm/examples/exec_on_tag.sh',
             self.workspace,
             'mpv',
             '--fs',
             '--loop=inf',
             '--no-terminal',
             self.filepath
             ]
        self.proc = subprocess.Popen(self.cmd)

    def try_show(self):
        if self.runner is not None:
            self.runner(self)

    def detect_type(self):
        filetype2callback = {
            'application/pdf': Page.show_pdf,
            'video/.*': Page.show_mpv,
        }
        xdg_mime = subprocess.run(['xdg-mime', 'query', 'filetype', self.filepath],
                                  stdout=subprocess.PIPE,
                                  universal_newlines=True)
        filetype = xdg_mime.stdout.strip()
        debug(f'\"{self.filepath}\" has type \"{filetype}\"')
        for type_re, callback in filetype2callback.items():
            if re.match(type_re, filetype):
                self.runner = callback
                break
        if self.runner is None:
            debug(f'Do not know how to handle filetype \"{filetype}\" of \"{self.filepath}\"')


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
        p.try_show()

    keep_running = True
    last_autoswitch_time = time.time()
    auto_page_switch = state.auto_page_switch()
    while keep_running:
        data_ready = select.select([], [], [], 1.0)[0]
        if run_posters.signal_received is not None:
            debug(f"Exiting because of signal {run_posters.signal_received}")
            keep_running = False
            break

        if auto_page_switch is not None and auto_page_switch > 0:
            time_now = time.time()
            time_since_last_autoswitch = time_now - last_autoswitch_time
            if time_since_last_autoswitch >= auto_page_switch:
                last_autoswitch_time = time_now
                cmd_text = """
                herbstclient and
                    , use_index +1
                    , compare tags.focus.client_count = 0
                    , use_index 0
                """
                cmd_args = shlex.split(cmd_text)
                # debug(f'Running: {cmd_args}')
                subprocess.run(cmd_args)

    # send termination signal to all:
    for p in pages:
        if p.proc is not None:
            p.proc.terminate()

    # wait for them to actually shut down:
    now = time.clock_gettime(time.CLOCK_MONOTONIC)
    # since all have received SIGTERM already, all processes
    # share the timeout:
    total_timeout = now + 20
    try:
        for p in pages:
            if p.proc is not None:
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
    parser.add_argument('--auto-page-switch',
                        help='automatically switch between pages within <n> seconds')
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

import itertools
import subprocess
import sys
import threading
from pathlib import Path
from typing import Optional

import appdirs
from subprocess import run, Popen

is_windows = sys.platform.startswith('win')

rent_manager_dirs = appdirs.AppDirs('RentManager')
user_cache = Path(rent_manager_dirs.user_cache_dir)
script_dir = Path(__file__).parent

conda_dir = user_cache / 'python' / 'miniconda'
launcher_venv = user_cache / 'python' / 'launcher_venv'

if is_windows:
    conda_exec = conda_dir / '_conda.exe'
    venv_dir_python_relative = 'python.exe'
else:
    conda_exec = conda_dir / 'bin' / 'conda'
    venv_dir_python_relative = Path('bin') / 'python'


def new_venv(destination, requirements, channels=()):
    destination.mkdir(parents=True)
    run([conda_exec, 'create', '-p', destination, 'python=3.9', '--yes', '--no-default-packages'], check=True)
    run([
        conda_exec, 'install', '-p', destination, '--file', requirements, '--yes',
        *itertools.chain.from_iterable(('-c', channel) for channel in channels)
    ], check=True)


def popen_in_venv(venv, command: list, **kwargs) -> Popen:
    streams = ('in', 'out', 'err')
    for stream in streams:
        kwargs['std' + stream] = subprocess.PIPE
    proc = Popen([conda_exec, 'run', '-p', venv, *command], **kwargs)
    for stream in ('out', 'err'):
        def echo(stream=stream):
            out = getattr(proc, 'std' + stream)
            for line in out:
                print(line.decode())

        t = threading.Thread(target=echo)
        t.start()

    return proc

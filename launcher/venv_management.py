import itertools
import subprocess
import sys
from pathlib import Path
from subprocess import run, Popen

import appdirs

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
    if is_windows:
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

    return Popen([conda_exec, 'run', '-p', venv, *command], **kwargs)

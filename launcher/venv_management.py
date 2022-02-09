import itertools
import subprocess
import sys
import threading
from pathlib import Path
from subprocess import Popen
import logging

import appdirs

is_windows = sys.platform.startswith('win')

rent_manager_dirs = appdirs.AppDirs('RentManager')
user_cache = Path(rent_manager_dirs.user_cache_dir)
script_dir = Path(__file__).parent

conda_dir = user_cache / 'python' / 'miniconda'
launcher_venv = user_cache / 'python' / 'launcher_venv'

LOG_STDERR = logging.INFO + 2
logging.addLevelName(LOG_STDERR, 'STDERR')
LOG_STDOUT = logging.INFO + 1
logging.addLevelName(LOG_STDOUT, 'STDOUT')

logger = logging.getLogger()

if is_windows:
    conda_exec = conda_dir / '_conda.exe'
    venv_dir_python_relative = 'python.exe'
else:
    conda_exec = conda_dir / 'bin' / 'conda'
    venv_dir_python_relative = Path('bin') / 'python'


def new_venv(destination, requirements, channels=()):
    destination.mkdir(parents=True)
    logged_run([conda_exec, 'create', '-p', destination, 'python=3.9', '--yes', '--no-default-packages'])
    logged_run([
        conda_exec, 'install', '-p', destination, '--file', requirements, '--yes',
        *itertools.chain.from_iterable(('-c', channel) for channel in channels)
    ])


def popen_in_venv(venv, command: list, **kwargs) -> Popen:
    if is_windows:
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

    return LoggedPopen([conda_exec, 'run', '-p', venv, *command], **kwargs)


def logged_run(args, **kwargs):
    with LoggedPopen(args, **kwargs) as process:
        pass

    return_code = process.poll()
    if return_code:
        raise subprocess.CalledProcessError(return_code, args)


class LoggedPopen(Popen):
    def __init__(self, args, **kwargs):
        kwargs['stdout'] = subprocess.PIPE
        kwargs['stderr'] = subprocess.PIPE
        super().__init__(args, **kwargs)

        def do_log(stream, level):
            with stream:
                for line in iter(stream.readline, b''):
                    logging.log(level, line)

        self.stdout_thread = threading.Thread(target=do_log, args=(self.stdout, LOG_STDOUT))
        self.stdout_thread.start()
        self.stderr_thread = threading.Thread(target=do_log, args=(self.stdout, LOG_STDERR))
        self.stderr_thread.start()

    def wait(self, timeout=None) -> int:
        self.stdout_thread.join()
        self.stderr_thread.join()

        return super().wait(timeout)

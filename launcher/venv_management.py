import subprocess
import sys
from pathlib import Path
from typing import Optional

import appdirs
from subprocess import run, Popen

is_windows = sys.platform.startswith('win')

rent_manager_dirs = appdirs.AppDirs('RentManager')
user_cache = Path(rent_manager_dirs.user_cache_dir)
script_dir = Path(__file__).parent

conda_dir = user_cache / 'python' / 'miniconda'
conda_venv_dir = user_cache / 'python' / 'conda_venv'
venv_dir = user_cache / 'python' / 'venv'

if is_windows:
    conda_exec = conda_dir / '_conda.exe'
    conda_venv_dir_python = conda_venv_dir / 'python.exe'
    venv_dir_python_relative = Path('Scripts') / 'python.exe'
else:
    conda_exec = conda_dir / 'bin' / 'conda'
    conda_venv_dir_python = conda_venv_dir / 'bin' / 'python'
    venv_dir_python_relative = Path('bin') / 'python'


def new_venv(destination, requirements):
    destination.mkdir(parents=True)
    run([conda_venv_dir_python, '-m', 'venv', destination], check=True)

    pip = [destination / venv_dir_python_relative, '-m', 'pip']
    install = [*pip, 'install', '-r', requirements]

    if is_windows:
        with ActivatedVenvPopen() as shell:
            shell.run([*pip, 'install', '--upgrade', 'pip'])
            shell.run(install)
    else:
        run(install, check=True)


class ActivatedVenvPopen:
    def __init__(self):
        activate = conda_dir / 'Scripts' / 'activate.bat'
        pipes = {f'std{handle}': subprocess.PIPE for handle in ['in', 'out', 'err']}

        self.popen: Optional[Popen]
        if is_windows:
            self.popen = Popen(f'cmd.exe "/K" {activate}', shell=True, **pipes)
        else:
            self.popen = None

    def __enter__(self):
        if is_windows:
            self.popen.__enter__()
        return self

    def run(self, command, cwd=None):
        if cwd is not None:
            self.run(['cd', cwd])

        command_str = ' '.join(str(part) for part in command)
        if is_windows:
            self.popen.stdin.write(command_str.encode())
            self.popen.stdin.write(b'\n')
            self.popen.stdin.flush()
        else:
            self.wait()
            self.popen = Popen(command_str, shell=True)

    def wait(self):
        if self.popen is not None:
            self.popen.wait()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if is_windows:
            self.popen.stdin.write(b'exit\n')
            self.popen.stdin.flush()

            for line in self.popen.stdout:
                print(line.decode())
            for line in self.popen.stderr:
                print(line.decode(), file=sys.stderr)

            self.popen.__exit__(exc_type, exc_val, exc_tb)


if __name__ == '__main__':
    run([venv_dir / venv_dir_python_relative, '-c',
         'from github import Github;print(list(Github().get_repo(\'olisolomons/rent_manager.py\').get_releases()))'])
    print('=' * 10)
    with ActivatedVenvPopen() as shell:
        shell.run([venv_dir / venv_dir_python_relative, '-c',
                   '"from github import Github;print(list(Github().get_repo(\'olisolomons/rent_manager.py\').get_releases()))"'])

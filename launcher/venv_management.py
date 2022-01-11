import subprocess
import sys
from pathlib import Path
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
        activate = conda_dir / 'Scripts' / 'activate.bat'
        pipes = {f'std{handle}': subprocess.PIPE for handle in ['in', 'out', 'err']}
        with Popen(f'cmd.exe "/K" {activate}', shell=True, **pipes) as conda_shell:
            commands = [
                [*pip, 'install', '--upgrade', 'pip'],
                install,
                ['exit']
            ]
            for command in commands:
                conda_shell.stdin.write(' '.join(command).encode())
                conda_shell.stdin.write(b'\n')
                conda_shell.stdin.flush()
    else:
        run(install, check=True)

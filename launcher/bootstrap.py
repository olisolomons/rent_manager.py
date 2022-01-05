import appdirs
from pathlib import Path
import shutil
import subprocess
from subprocess import run
import sys

is_windows = sys.platform.startswith('win')

rent_manager_dirs = appdirs.AppDirs('RentManager')
user_cache = Path(rent_manager_dirs.user_cache_dir)
script_dir = Path(__file__).parent

bootstrap_complete_marker = user_cache / 'bootstrap_complete'

conda_dir = user_cache / 'python' / 'miniconda'
conda_venv_dir = user_cache / 'python' / 'conda_venv'
venv_dir = user_cache / 'python' / 'venv'

if is_windows:
    conda_exec = conda_dir / '_conda.exe'
    conda_venv_dir_python = conda_venv_dir / 'python.exe'
    venv_dir_python = venv_dir / 'Scripts' / 'python.exe'
else:
    conda_exec = conda_dir / 'bin' / 'conda'
    conda_venv_dir_python = conda_venv_dir / 'bin' / 'python'
    venv_dir_python = venv_dir / 'bin' / 'python'

requirements = script_dir / 'launcher_requirements.txt'


def bootstrap():
    if bootstrap_complete_marker.exists():
        return

    shutil.rmtree(user_cache / 'python', ignore_errors=True)
    (user_cache / 'python').mkdir(parents=True)

    if is_windows:
        run([script_dir / 'miniconda.exe', '/InstallationType=JustMe', 'RegisterPython=0', '/S',
             f'/D={conda_dir}'], check=True)
    else:
        run(['/usr/bin/env', 'sh', script_dir / 'miniconda.sh', '-b', '-p', conda_dir], check=True)

    run([conda_exec, 'create', '-p', conda_venv_dir, 'python=3.9', '--yes'], check=True)

    venv_dir.mkdir(parents=True)
    run([conda_venv_dir_python, '-m', 'venv', venv_dir], check=True)
    run([venv_dir_python, '-m', 'pip', 'install', '-r', requirements], check=True)

    bootstrap_complete_marker.touch()


if __name__ == '__main__':
    bootstrap()
    subprocess.run([venv_dir / 'bin' / 'python', script_dir / 'main.py', *sys.argv[1:]])

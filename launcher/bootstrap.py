import appdirs
from pathlib import Path
import shutil
import subprocess
from subprocess import run
import sys

rent_manager_dirs = appdirs.AppDirs('RentManager')
user_data = Path(rent_manager_dirs.user_data_dir)
script_dir = Path(__file__).parent

bootstrap_complete_marker = user_data / 'bootstrap_complete'
conda_dir = user_data / 'python' / 'miniconda'
conda_venv_dir = user_data / 'python' / 'conda_venv'
venv_dir = user_data / 'python' / 'venv'
requirements = script_dir / 'launcher_requirements.txt'

miniconda_url = 'https://repo.anaconda.com/miniconda/Miniconda3-py39_4.9.2-MacOSX-x86_64.sh'


def bootstrap():
    if bootstrap_complete_marker.exists():
        return

    shutil.rmtree(user_data / 'python', ignore_errors=True)
    (user_data / 'python').mkdir(parents=True)

    install_script = user_data / 'python' / 'miniconda.sh'

    run(['/usr/bin/wget', miniconda_url, '-O', install_script], check=True)
    run(['/usr/bin/env', 'sh', install_script, '-b', '-p', conda_dir], check=True)
    run([conda_dir / 'bin' / 'conda', 'create', '-p', conda_venv_dir, 'python=3.9', '--yes'], check=True)

    venv_dir.mkdir(parents=True)
    run([conda_venv_dir / 'bin' / 'python', '-m', 'venv', venv_dir], check=True)
    run([venv_dir / 'bin' / 'python', '-m', 'pip', 'install', '-r', requirements], check=True)

    bootstrap_complete_marker.touch()


if __name__ == '__main__':
    bootstrap()
    subprocess.run([venv_dir / 'bin' / 'python', script_dir / 'main.py', *sys.argv[1:]])

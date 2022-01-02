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


def bootstrap():
    if bootstrap_complete_marker.exists():
        return

    shutil.rmtree(user_data / 'python', ignore_errors=True)
    (user_data / 'python').mkdir(parents=True)

    print(f"{(script_dir / 'miniconda.sh')=}; {(script_dir / 'miniconda.sh').is_file()=}")
    res = run(['/usr/bin/env', 'sh', str(script_dir / 'miniconda.sh'), '-b', '-p', str(conda_dir)])
    print(res.returncode)
    res.check_returncode()

    run([conda_dir / 'bin' / 'conda', 'create', '-p', conda_venv_dir, 'python=3.9', '--yes'], check=True)

    venv_dir.mkdir(parents=True)
    run([conda_venv_dir / 'bin' / 'python', '-m', 'venv', venv_dir], check=True)
    run([venv_dir / 'bin' / 'python', '-m', 'pip', 'install', '-r', requirements], check=True)

    bootstrap_complete_marker.touch()


if __name__ == '__main__':
    bootstrap()
    subprocess.run([venv_dir / 'bin' / 'python', script_dir / 'main.py', *sys.argv[1:]])

import appdirs
from pathlib import Path
import shutil
import subprocess
import venv
import sys

rent_manager_dirs = appdirs.AppDirs('RentManager')
user_data = Path(rent_manager_dirs.user_data_dir)
script_dir = Path(__file__).parent

bootstrap_complete_marker = user_data / 'bootstrap_complete'
launcher_dir = user_data / 'launcher'
launcher_script = script_dir / 'main.py'
requirements = script_dir / 'launcher_requirements.txt'

launcher_bin = launcher_dir / 'venv' / 'bin'


def bootstrap():
    if bootstrap_complete_marker.exists():
        return

    shutil.rmtree(launcher_dir, ignore_errors=True)
    launcher_dir.mkdir(parents=True)

    shutil.copy(launcher_script, launcher_dir)

    (launcher_dir / 'venv').mkdir()
    venv.create(launcher_dir / 'venv', with_pip=True)

    subprocess.run([launcher_bin / 'pip', 'install', '-r', requirements], check=True)

    bootstrap_complete_marker.touch()


if __name__ == '__main__':
    bootstrap()
    subprocess.run([launcher_bin / 'python', launcher_dir / 'main.py', *sys.argv[1:]])

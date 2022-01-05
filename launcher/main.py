import re
import shutil
import time
from subprocess import run
from typing import Optional
import simple_ipc

from github import Github
import requests
from zipfile import ZipFile
import io
import appdirs
from pathlib import Path
import sys

is_windows = sys.platform.startswith('win')

rent_manager_dirs = appdirs.AppDirs('RentManager')
user_cache = Path(rent_manager_dirs.user_cache_dir)

conda_venv_dir = user_cache / 'python' / 'conda_venv'
venv_dir = user_cache / 'python' / 'venv'

if is_windows:
    conda_venv_dir_python = conda_venv_dir / 'python.exe'
    venv_dir_python_relative = Path('Scripts') / 'python.exe'
else:
    conda_venv_dir_python = conda_venv_dir / 'bin' / 'python'
    venv_dir_python_relative = Path('bin') / 'python'

install_complete_marker = 'install_complete_marker'


def parse_release(release_name: str) -> list[int]:
    pattern = re.compile(r'^v(\d+)\.(\d+)\.(\d+)$')
    match = pattern.match(release_name)
    return [int(group) for group in match.groups()]


def get_latest_release() -> Optional[Path]:
    """
    Get the latest_release release, deleting all older releases or incomplete installs
    :return: The latest_release release directory, or None if there is no complete installed release
    """
    releases_dir = user_cache / 'releases'
    if not releases_dir.is_dir():
        return

    releases = sorted(releases_dir.iterdir(), key=lambda release_dir: parse_release(release_dir.name))
    latest = None
    for release in releases:
        if latest is None and (release / install_complete_marker).is_file():
            latest = release
        else:
            shutil.rmtree(release)

    return latest


def install_latest_release() -> Path:
    """
    Install the latest_release release
    :return: The directory into which the release was installed
    """
    yield 'Finding latest release'
    g = Github()
    repo = g.get_repo('olisolomons/rent_manager.py')
    release = next(iter(repo.get_releases()))

    yield f'Setup for release {release.tag_name}'

    # prepare directory
    release_dir = user_cache / 'releases' / release.tag_name
    shutil.rmtree(release_dir, ignore_errors=True)
    release_dir.mkdir(parents=True, exist_ok=True)

    yield f'Downloading release {release.tag_name}'

    # download and extract
    resp = requests.get(release.zipball_url).content
    yield 'Unpacking'
    zipfile = ZipFile(io.BytesIO(resp))
    zipfile.extractall(release_dir)

    zip_contents = next(release_dir.iterdir())
    for item in list(zip_contents.iterdir()):
        shutil.move(item, release_dir)
    zip_contents.rmdir()

    yield f'Installing release {release.tag_name}'

    # prepare venv
    release_venv = release_dir / 'venv'
    release_venv.mkdir()

    run([conda_venv_dir_python, '-m', 'venv', release_venv], check=True)
    run([release_venv / venv_dir_python_relative, '-m', 'pip', 'install', '-r', release_dir / 'requirements.txt'],
        check=True)

    yield 'Finishing application installation'
    (release_dir / install_complete_marker).touch()

    return release_dir


def run_application(release_dir: Path) -> None:
    release_venv = release_dir / 'venv'
    run([release_venv / venv_dir_python_relative, 'main.py', *sys.argv[2:]], check=True, cwd=release_dir / 'src')


def install_and_launch():
    latest_release = get_latest_release()
    if latest_release is None:
        latest_release = yield from install_latest_release()
    yield {'type': 'close_window'}
    run_application(latest_release)


def test_task2():
    yield 'Now in test_task2'
    time.sleep(1.5)
    yield 'It\'s working!'
    time.sleep(0.75)
    # raise Exception('it\'s not working!')
    yield {'type': 'close_window'}
    for i in range(10):
        print(f'{i=} main.py')
        time.sleep(0.5)


if __name__ == '__main__':
    print(f'{sys.argv=}')
    port = int(sys.argv[1])
    with simple_ipc.get_sock() as sock:
        client = simple_ipc.Client(sock, port)
        client.run(install_and_launch())

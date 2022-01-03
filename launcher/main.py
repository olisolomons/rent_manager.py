import re
import shutil
from subprocess import run
from typing import Optional

from github import Github
import requests
from zipfile import ZipFile
import io
import appdirs
from pathlib import Path
import sys

rent_manager_dirs = appdirs.AppDirs('RentManager')
user_cache = Path(rent_manager_dirs.user_cache_dir)

conda_venv_dir = user_cache / 'python' / 'conda_venv'
venv_dir = user_cache / 'python' / 'venv'

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
    # get latest_release release
    g = Github()
    repo = g.get_repo('olisolomons/rent_manager.py')
    release = next(iter(repo.get_releases()))

    # prepare directory
    release_dir = user_cache / 'releases' / release.tag_name
    shutil.rmtree(release_dir, ignore_errors=True)
    release_dir.mkdir(parents=True, exist_ok=True)

    # download and extract
    resp = requests.get(release.zipball_url).content
    zipfile = ZipFile(io.BytesIO(resp))
    zipfile.extractall(release_dir)

    # prepare venv
    release_venv = release_dir / 'venv'
    release_venv.mkdir()

    run([conda_venv_dir / 'bin' / 'python', '-m', 'venv', release_venv], check=True)
    run([release_venv / 'bin' / 'python', '-m', 'pip', 'install', '-r', release_dir / 'requirements.txt'], check=True)

    return release_dir


def run_application(release_dir: Path) -> None:
    release_venv = release_dir / 'venv'
    run([release_venv / 'bin' / 'python', 'main.py', *sys.argv[1:]], check=True, cwd=release_dir / 'src')


if __name__ == '__main__':
    latest_release = get_latest_release()
    if latest_release is None:
        latest_release = install_latest_release()
    run_application(latest_release)

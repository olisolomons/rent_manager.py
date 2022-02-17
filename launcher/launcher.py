import argparse
import io
import logging
import re
import shutil
import socket
import traceback
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional, Generator, Union, TypeVar, Any, Callable
from zipfile import ZipFile

import simple_ipc
import venv_management
from venv_management import user_cache, venv_dir_python_relative, rent_manager_dirs, LoggedProcess

install_complete_marker = 'install_complete_marker'

parser = argparse.ArgumentParser()
parser.add_argument('file', help='the file to open', nargs='?')
parser.add_argument('--port', help='port for communicating with installer process')
parser.add_argument('--no-app', action='store_true', help='don\'t run the app, but instead print the app_server port')

log_dir = Path(rent_manager_dirs.user_log_dir)
log_dir.mkdir(parents=True, exist_ok=True)

handler = TimedRotatingFileHandler(
    filename=log_dir / 'launcher', when='D', backupCount=15, encoding='utf-8', delay=False
)

logging.basicConfig(
    format='[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
    handlers=[handler],
    level=logging.INFO
)


def parse_release(release_name: str) -> list[int]:
    pattern = re.compile(r'^v(\d+)\.(\d+)\.(\d+)$')
    match = pattern.match(release_name)
    return [int(group) for group in match.groups()]


def get_latest_installed_release() -> Optional[Path]:
    """
    Get the latest_release release, deleting all older releases or incomplete installs
    :return: The latest_release release directory, or None if there is no complete installed release
    """
    releases_dir = user_cache / 'releases'
    if not releases_dir.is_dir():
        return

    releases = sorted(releases_dir.iterdir(), key=lambda release_dir: parse_release(release_dir.name), reverse=True)
    latest = None
    for release in releases:
        if latest is None and (release / install_complete_marker).is_file():
            latest = release
        else:
            shutil.rmtree(release)

    return latest


def get_latest_release():
    from github import Github
    g = Github()
    repo = g.get_repo('olisolomons/rent_manager.py')
    return next(iter(repo.get_releases()))


def install_latest_release() -> Generator[str, Any, LoggedProcess]:
    """
    Install the latest_release release
    :return: The directory into which the release was installed
    """
    import requests

    yield 'Finding latest release'
    release = get_latest_release()

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
    venv_management.new_venv(release_venv, release_dir / 'requirements.txt', channels=['conda-forge'])

    yield 'Finishing application installation'
    (release_dir / install_complete_marker).touch()

    return release_dir


def run_application(release_dir: Path, file: Optional[str], port: int) -> LoggedProcess:
    release_venv = release_dir / 'venv'

    popen = venv_management.popen_in_venv(
        release_venv,
        [
            release_venv / venv_dir_python_relative, 'main.py',
            '--port', str(port),
            *(() if file is None else (file,))
        ],
        cwd=release_dir / 'src'
    )

    return popen


T = TypeVar('T')
U = TypeVar('U')


def generator_return_value(g: Generator[T, Any, U]) -> tuple[Generator[T, Any, U], Callable[[], U]]:
    return_value: Optional[U] = None

    def proxy_generator() -> Generator[T, Any, U]:
        nonlocal return_value
        return_value = yield from g
        return return_value

    def get() -> U:
        return return_value

    return proxy_generator(), get


def install_and_launch(file: str, app_server_port: int) -> Generator[Union[str, dict], None, LoggedProcess]:
    latest_release = get_latest_installed_release()
    if latest_release is None:
        latest_release = yield from install_latest_release()
    yield simple_ipc.CLOSE_WINDOW
    return run_application(latest_release, file, app_server_port)


def main():
    args = parser.parse_args()
    get_app_process: Optional[Callable] = None
    installer_client_sock: Optional[socket.socket] = None

    def run_with_server(runner):
        nonlocal get_app_process, installer_client_sock

        restart_on_close = False

        with simple_ipc.get_sock() as app_server_sock:
            app_server = simple_ipc.Server(app_server_sock)

            if not args.no_app:
                install_and_launch_generator, get_app_process = generator_return_value(
                    install_and_launch(args.file, app_server.port)
                )
                runner(install_and_launch_generator)
            else:
                print(f'{app_server.port=}')

            while True:
                try:
                    channel = app_server.accept()
                    break
                except socket.timeout:
                    if get_app_process:
                        app_process: venv_management.BaseLoggedProcess = get_app_process()
                        if app_process.return_code is not None:
                            raise

            if installer_client_sock is not None:
                installer_client_sock.close()
                installer_client_sock = None

            for app_message in app_server.recv_all(channel):
                print(f'{app_message=}')
                if app_message['type'] == 'latest_version':
                    channel.send({'type': 'latest_version', 'value': get_latest_release().tag_name})
                elif app_message['type'] == 'do_update':
                    try:
                        for step in install_latest_release():
                            channel.send({'type': 'install_status', 'value': step})
                    except Exception:
                        tb = traceback.format_exc()
                        channel.send({'type': 'error', 'value': tb})
                    else:
                        channel.send(simple_ipc.CLOSE_WINDOW)
                elif app_message['type'] == 'restart':
                    restart_on_close = True
                    if get_app_process:
                        app_process = get_app_process()
                        app_process.wait()

        if restart_on_close:
            run_with_server(runner)

    if args.port:
        with simple_ipc.get_sock() as installer_client_sock:
            client = simple_ipc.Client(installer_client_sock, int(args.port))

            def runner(install_and_launch_generator):
                if installer_client_sock is not None:
                    client.run(install_and_launch_generator)
                else:
                    for step in install_and_launch_generator:
                        print(step)

            run_with_server(runner)
    else:
        def runner(install_and_launch_generator):
            for step in install_and_launch_generator:
                print(step)

        run_with_server(runner)

    if get_app_process is not None:
        app_process = get_app_process()
        app_process.wait()


if __name__ == '__main__':
    main()

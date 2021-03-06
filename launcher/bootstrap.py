import logging
import multiprocessing
import queue
import shutil
import socket
import sys
import threading
import time
import tkinter as tk
import traceback
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

import simple_ipc
import venv_management
from venv_management import rent_manager_dirs, LoggedProcess
from venv_management import user_cache, script_dir, is_windows, conda_dir, launcher_venv, launcher_files_dir, \
    venv_dir_python_relative

bootstrap_complete_marker = user_cache / 'bootstrap_complete'
conda_installed_marker = user_cache / 'conda_installed'

log_dir = Path(rent_manager_dirs.user_log_dir)
log_dir.mkdir(parents=True, exist_ok=True)

handler = TimedRotatingFileHandler(filename=log_dir / 'boot', when='D', backupCount=15, encoding='utf-8', delay=False)

logging.basicConfig(
    format='[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
    handlers=[handler, logging.StreamHandler(sys.stdout)],
    level=logging.DEBUG
)

launcher_files = [
    script_dir / 'launcher.py',
    script_dir / 'simple_ipc.py',
    script_dir / 'venv_management.py',
]


def bootstrap():
    if bootstrap_complete_marker.exists():
        return

    if not conda_installed_marker.exists():
        yield 'Installing python'

        shutil.rmtree(user_cache / 'python', ignore_errors=True)
        (user_cache / 'python').mkdir(parents=True)

        if is_windows:
            LoggedProcess.run([
                script_dir / 'miniconda.exe', '/InstallationType=JustMe', 'RegisterPython=0', '/S', f'/D={conda_dir}'
            ])
        else:
            LoggedProcess.run(['/usr/bin/env', 'sh', script_dir / 'miniconda.sh', '-b', '-p', conda_dir])

        conda_installed_marker.touch()
    else:
        for item in (user_cache / 'python').iterdir():
            if item == conda_dir:
                continue

            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    yield 'Copying launcher'
    launcher_files_dir.mkdir()
    for launcher_file in launcher_files:
        shutil.copy(launcher_file, launcher_files_dir)

    yield 'Installing launcher'
    venv_management.new_venv(launcher_venv, script_dir / 'launcher_requirements.txt', channels=['conda-forge'])

    yield 'Finishing launcher installation'
    bootstrap_complete_marker.touch()


def test_task():
    from shutil import which
    yield 'Task a'
    time.sleep(0.5)
    yield 'Task b'
    time.sleep(0.5)
    with simple_ipc.get_sock() as sock:
        server = simple_ipc.Server(sock)
        code = """
import simple_ipc
import sys
import time
import tkinter as tk
from threading import Thread

print(sys.argv)

def test():
    yield 'Alien'
    time.sleep(0.5)
    yield 'Thing'
    time.sleep(1)
    # int(int)
    yield simple_ipc.CLOSE_WINDOW

def msgs():
    with simple_ipc.get_sock() as installer_client_sock:
        client = simple_ipc.Client(installer_client_sock, int(sys.argv[1]))
        client.run(test())
        # int(int)

msgs()



# t=Thread(target=msgs)
# root=tk.Tk()
# root.after(500,lambda:print('stuff'))
# root.after(1000,t.start)
# 
# root.after(10000,root.destroy)
# 
# root.mainloop()


"""
        proc = LoggedProcess.popen([which('python'), '-c', code, str(server.port)])
        while True:
            try:
                yield from server.recv_all()
                break
            except socket.timeout:
                if proc.return_code is not None:
                    yield {'type': 'error', 'traceback': 'Unable to connect to launcher'}
                    break

        print('closing sock')
    print('waiting')
    time.sleep(1)
    proc.detach()


class InstallerApp(tk.Tk):
    def __init__(self, task_function):
        super().__init__()
        self.title('Rent Manager - Installing')
        self.grid_columnconfigure(0, weight=1)

        self.progress = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=100, mode='indeterminate')
        self.progress.grid(padx=20, pady=20, sticky=tk.E + tk.W)

        self.current_task = tk.Label(self, text='Starting installer')
        self.current_task.grid(row=1, column=0, pady=20)

        self.current_task_queue = queue.Queue()
        self.task_thread = threading.Thread(target=self.run_task, args=(task_function,))
        self.task_thread.start()

        self.update_progress()

    def update_progress(self):
        self.progress['value'] += 5
        if not self.current_task_queue.empty():
            task = self.current_task_queue.get()
            if isinstance(task, str):
                self.current_task.config(text=task)
            elif task == simple_ipc.CLOSE_WINDOW:
                self.destroy()
                return

            elif task['type'] == 'error':
                self.progress.destroy()
                self.current_task.destroy()
                tb = task['traceback']

                message = ScrolledText(self)
                message.insert(tk.CURRENT, f'An error has occurred. '
                                           f'Please copy this text and send it to the developer:\n\n'
                                           f'{tb}\n{rent_manager_dirs.user_log_dir=}')
                # noinspection SpellCheckingInspection
                message.grid(row=0, column=0, sticky='NESW')
                message.config(state=tk.DISABLED)
                message.bind("<1>", lambda _event: message.focus_set())

                def copy_traceback():
                    self.clipboard_clear()
                    self.clipboard_append(tb)

                copy_button = tk.Button(self, text='Copy to clipboard', command=copy_traceback)
                copy_button.grid(row=1, column=0, sticky='EW')
                self.grid_rowconfigure(0, weight=1)
                return

        self.after(50, self.update_progress)

    def run_task(self, task_function):
        task = task_function()
        try:
            for current_step in task:
                self.current_task_queue.put(current_step)
                if current_step == simple_ipc.CLOSE_WINDOW:
                    break
            list(task)  # exhaust generator to unsure it completes
            self.current_task_queue.put(simple_ipc.CLOSE_WINDOW)
        except Exception:
            self.current_task_queue.put({'type': 'error', 'traceback': traceback.format_exc()})

    def mainloop(self, n=0):
        super().mainloop()

        self.task_thread.join()


def bootstrap_and_run():
    logging.info('Starting')
    yield from bootstrap()
    yield 'Installed launcher...\nPlease wait for launcher to start'
    logging.debug('Creating socket')
    with simple_ipc.get_sock() as sock:
        logging.debug('Setting up socket')
        server = simple_ipc.Server(sock)
        logging.debug('Starting process')
        launcher: venv_management.BaseLoggedProcess = venv_management.popen_in_venv(
            launcher_venv,
            [launcher_venv / venv_dir_python_relative, 'launcher.py', '--port', str(server.port), *sys.argv[1:]],
            cwd=launcher_files_dir
        )
        logging.info('Started launcher process')
        while True:
            try:
                logging.info('Connecting to launcher socket')
                yield from server.recv_all()
                break
            except socket.timeout:
                if launcher.return_code is not None:
                    logging.error(
                        f'Timed out connecting to launcher socket: '
                        f'process finished with code {launcher.return_code}'
                    )
                    yield {'type': 'error', 'traceback': 'Unable to connect to launcher'}
                    break
                logging.warning('Timed out connecting to launcher socket, trying again')

    if is_windows:
        logging.debug('Waiting for launcher to complete')
        launcher.wait()
    else:
        logging.debug('Detaching from launcher')
        launcher.detach()


def main():
    app = InstallerApp(bootstrap_and_run)
    app.geometry('300x200')

    app.mainloop()


if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()

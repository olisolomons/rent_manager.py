import queue
import threading
import time
import traceback

import appdirs
from pathlib import Path
import shutil
import subprocess
from subprocess import run
import sys
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import simple_ipc

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

    yield 'Installing python'

    shutil.rmtree(user_cache / 'python', ignore_errors=True)
    (user_cache / 'python').mkdir(parents=True)

    if is_windows:
        run([script_dir / 'miniconda.exe', '/InstallationType=JustMe', 'RegisterPython=0', '/S',
             f'/D={conda_dir}'], check=True)
    else:
        run(['/usr/bin/env', 'sh', script_dir / 'miniconda.sh', '-b', '-p', conda_dir], check=True)

    yield 'Setting up launcher'

    run([conda_exec, 'create', '-p', conda_venv_dir, 'python=3.9', '--yes'], check=True)

    yield 'Installing launcher'
    venv_dir.mkdir(parents=True)
    run([conda_venv_dir_python, '-m', 'venv', venv_dir], check=True)
    run([venv_dir_python, '-m', 'pip', 'install', '-r', requirements], check=True)

    yield 'Finishing launcher installation'
    bootstrap_complete_marker.touch()


CLOSE_WINDOW = {'type': 'close_window'}


def test_task():
    yield 'Task a'
    time.sleep(1)
    yield 'Task b'
    time.sleep(3)
    with simple_ipc.get_sock() as sock:
        server = simple_ipc.Server(sock)
        proc = subprocess.Popen(['/usr/bin/env', 'python3', 'main.py', str(server.port)])
        yield from server.recv_all()
    proc.wait()


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
            elif task == CLOSE_WINDOW:
                self.destroy()
                return

            elif task['type'] == 'error':
                self.progress.destroy()
                self.current_task.destroy()
                tb = task['traceback']

                message = ScrolledText(self)
                message.insert(tk.CURRENT, f'An error has occurred. '
                                           f'Please copy this text and send it to the developer:\n\n{tb}')
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
            self.current_task_queue.put(CLOSE_WINDOW)
        except Exception:
            self.current_task_queue.put({'type': 'error', 'traceback': traceback.format_exc()})

    def mainloop(self, n=0):
        super().mainloop()

        self.task_thread.join()


def bootstrap_and_run():
    yield from bootstrap()
    yield 'Installed launcher...\nPlease wait for launcher to start'
    with simple_ipc.get_sock() as sock:
        server = simple_ipc.Server(sock)
        subprocess.Popen([venv_dir / 'bin' / 'python', 'main.py', str(server.port), *sys.argv[1:]],
                         cwd=script_dir)
        yield from server.recv_all()


def main():
    app = InstallerApp(bootstrap_and_run)
    app.geometry('300x200')

    app.mainloop()


if __name__ == '__main__':
    main()

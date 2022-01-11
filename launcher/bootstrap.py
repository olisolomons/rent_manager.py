import queue
import threading
import time
import traceback

import shutil
import subprocess
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import simple_ipc
import venv_management
from venv_management import user_cache, script_dir, is_windows, conda_dir, conda_exec, conda_venv_dir, venv_dir
import sys
from subprocess import run

bootstrap_complete_marker = user_cache / 'bootstrap_complete'
conda_installed_marker = user_cache / 'conda_installed'

def bootstrap():
    if bootstrap_complete_marker.exists():
        return
    
    if not conda_installed_marker.exists():
        yield 'Installing python'

        shutil.rmtree(user_cache / 'python', ignore_errors=True)
        (user_cache / 'python').mkdir(parents=True)

        if is_windows:
            run([script_dir / 'miniconda.exe', '/InstallationType=JustMe', 'RegisterPython=0', '/S',
                 f'/D={conda_dir}'], check=True)
        else:
            run(['/usr/bin/env', 'sh', script_dir / 'miniconda.sh', '-b', '-p', conda_dir], check=True)
        
        conda_installed_marker.touch()

    yield 'Setting up launcher'

    run([conda_exec, 'create', '-p', conda_venv_dir, 'python=3.9', '--yes'], check=True)

    yield 'Installing launcher'
    venv_management.new_venv(venv_dir, script_dir / 'launcher_requirements.txt')

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

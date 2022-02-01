import queue
import threading
import tkinter as tk
import typing
from tkinter import messagebox
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from typing import Optional

import tk_utils

if typing.TYPE_CHECKING:
    import simple_ipc


def check_for_updates(root: tk.Misc, client: 'simple_ipc.Channel', current_version: str):
    client.send({'type': 'latest_version'})
    latest_version: str = client.recv()['value']

    from launcher import parse_release

    if current_version is None:
        messagebox.showinfo('Updates', f'Latest version is {latest_version}. Unable to detect current '
                                       f'version.')
    else:
        if parse_release(current_version) < parse_release(latest_version):
            class UpdaterDialog(tk.Toplevel):
                def __init__(self):
                    super().__init__(root)
                    self.title('Updates')
                    self.geometry('400x200')
                    self.focus_set()

                    self.progress = None
                    self.body_frame: Optional[tk.Frame] = None
                    self.reset_body()

                    message = tk.Message(
                        self.body_frame,
                        text=f'A new version is available! Would you like to update to {latest_version}?',
                    )
                    message.pack(fill=tk.BOTH, expand=True)

                    self.body_frame.bind('<Configure>', lambda e: message.config(width=e.width - 10))

                    button_box = tk.Frame(self)
                    button_box.grid(row=1, column=0)

                    self.update_button = tk.Button(button_box, text="Update", command=self.update_app)
                    self.update_button.pack(side=tk.LEFT, padx=5, pady=5)
                    w = tk.Button(button_box, text="Cancel", command=self.cancel)
                    w.pack(side=tk.LEFT, padx=5, pady=5)

                    self.bind("<Return>", lambda e: self.update_button.invoke())
                    self.bind("<Escape>", lambda e: self.cancel())

                    self.grid_rowconfigure(0, weight=1)
                    self.grid_columnconfigure(0, weight=1)

                def update_app(self):
                    self.update_button.config(state=tk.DISABLED)
                    client.send({'type': 'do_update'})
                    self.reset_body()

                    self.progress = ttk.Progressbar(self.body_frame, orient=tk.HORIZONTAL, length=100,
                                                    mode='indeterminate')
                    self.progress.grid(padx=20, pady=20, sticky=tk.E + tk.W)

                    current_task = tk.Label(self.body_frame, text='Starting updates')
                    current_task.grid(row=1, column=0, pady=20)

                    done = False
                    error_traceback = None

                    def run_task():
                        nonlocal done, error_traceback
                        while not done:
                            message = client.recv()

                            if message['type'] == 'close_window':
                                done = True
                            elif message['type'] == 'error':
                                done = True
                                error_traceback = message['value']

                            current_task_queue.put(message)

                    current_task_queue = queue.Queue()
                    task_thread = threading.Thread(target=run_task)

                    task_thread.start()

                    def update_progress():
                        self.progress['value'] += 5
                        if not current_task_queue.empty():
                            task = current_task_queue.get()
                            if task['type'] == 'install_status':
                                current_task.config(text=task['value'])

                        if done:
                            if error_traceback:
                                self.error_report(error_traceback)
                            else:
                                self.done_update()
                        else:
                            self.after(50, update_progress)

                    update_progress()

                def done_update(self):
                    self.reset_body()

                    message = tk.Message(self.body_frame, text='Update installed! Restart the application to use the '
                                                               'new version, or cancel to continue using the program.')
                    message.grid(row=0, column=0, sticky=tk_utils.STICKY_ALL)

                    self.body_frame.bind('<Configure>', lambda e: message.config(width=e.width - 10))

                    self.update_button.config(text='Restart app now', command=self.restart, state=tk.NORMAL)

                def error_report(self, error_traceback):
                    self.update_button.destroy()

                    class DummyUpdateButton:
                        def invoke(self):
                            pass

                    self.update_button = DummyUpdateButton()

                    message = ScrolledText(self.body_frame)
                    message.insert(tk.CURRENT, f'An error has occurred. '
                                               f'Please copy this text and send it to the developer:\n\n{error_traceback}')
                    message.grid(row=0, column=0, sticky='NESW')
                    message.config(state=tk.DISABLED)
                    message.bind("<1>", lambda _event: message.focus_set())

                    def copy_traceback():
                        self.clipboard_clear()
                        self.clipboard_append(error_traceback)

                    copy_button = tk.Button(self.body_frame, text='Copy to clipboard', command=copy_traceback)
                    copy_button.grid(row=1, column=0, sticky='EW')

                def reset_body(self):
                    self.progress = None
                    if self.body_frame:
                        self.body_frame.destroy()
                    self.body_frame = tk.Frame(self)
                    self.body_frame.grid(row=0, column=0, sticky=tk_utils.STICKY_ALL)
                    self.body_frame.grid_columnconfigure(0, weight=1)
                    self.body_frame.grid_rowconfigure(0, weight=1)

                def restart(self):
                    client.send({'type': 'restart'})
                    self.destroy()
                    root.winfo_toplevel().destroy()

                def cancel(self):
                    self.destroy()

            updater_dialog = UpdaterDialog()
            updater_dialog.wait_visibility()
            updater_dialog.grab_set()
            updater_dialog.wait_window(updater_dialog)



        else:
            messagebox.showinfo('Updates', f'Latest version is {latest_version}. You are already on the '
                                           f'latest version.')

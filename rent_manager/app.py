import dataclasses
import sys
from pathlib import Path
from typing import Callable, Optional
import enum

import tkinter as tk
from tkinter import filedialog
from tkinter import simpledialog

import dataclass_json
from . import config
from .menu import DocumentManager

from .state.rent_manager_state import RentManagerState


class UnsavedChangesResult(enum.Enum):
    Save = enum.auto()
    Continue = enum.auto()
    Cancel = enum.auto()


def unsaved_changes_dialog(parent):
    dialog = simpledialog.SimpleDialog(
        parent, 'There are unsaved changes. Would you like to save them or continue and lose them?',
        [opt.name for opt in UnsavedChangesResult],
        title='Unsaved Changes',
        cancel=UnsavedChangesResult.Cancel.value - 1
    )
    return list(UnsavedChangesResult)[dialog.go()]


class RentManagerApp(DocumentManager):
    def __init__(self, parent) -> None:
        self._frame = tk.Frame(parent)

        self._frame.grid_columnconfigure(0, weight=1)
        self._frame.grid_rowconfigure(0, weight=1)

        self.data = RentManagerState([], [])
        self.file_path: Optional[str] = None
        self.changed = False

        self.view = self.data.view()
        self.view.change_listeners.add(self.on_change)
        self.view.editing = True
        self.w = self.view(self._frame)
        self.w.grid(sticky='NESW')

        self.bind_key(self.save)
        self.bind_key(self.save_as, shift=True)
        self.bind_key(self.new)
        self.bind_key(self.open)
        self.bind_key(self.undo, key='z')
        self.bind_key(self.redo, key='y')
        self.bind_key(self.redo, key='z', shift=True)

        self._config = config.load()

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, new_config):
        self._config = new_config
        config.save(self._config)

    def bind_key(self, func: Callable[[], None], key: Optional[str] = None, shift: bool = False):
        ctrl = 'Meta_L' if sys.platform == 'darwin' else 'Control'
        shift_str = '-Shift' if shift else ''
        if key is None:
            key = func.__name__[0]
        if shift:
            key = key.upper()
        sequence = f'<{ctrl}{shift_str}-{key}>'
        self.frame.bind_all(sequence, lambda e: func())

    @property
    def frame(self) -> tk.Frame:
        return self._frame

    def on_change(self, new_state):
        self.changed = True
        print(new_state)

    def filedialog(self, dialog):
        top = self.frame.winfo_toplevel()

        initial_dir = str(Path.home())
        if self.config.file_chooser_dir is not None:
            initial_dir = self.config.file_chooser_dir

        res = dialog(parent=top, initialdir=initial_dir, filetypes=[('RentManager File', '*.rman')])

        if res:
            self.config = dataclasses.replace(self.config, file_chooser_dir=str(Path(res).parent))

        if res:
            return res
        else:
            return None

    def save(self):
        if self.file_path is None:
            self.save_as()
        else:
            state = self.view.get_state()
            with open(self.file_path, 'w') as f:
                dataclass_json.dump(state, f)
            self.changed = False

    def save_as(self):
        file_path = self.filedialog(filedialog.asksaveasfilename)
        if file_path is not None:
            self.file_path = file_path
            self.save()

    def prompt_unsaved_changes(self):
        if not self.changed:
            return False

        result = unsaved_changes_dialog(self.frame.winfo_toplevel())
        Res = UnsavedChangesResult
        if result is Res.Save:
            self.save()
            return False
        elif result is Res.Continue:
            return False
        elif result is Res.Cancel:
            return True
        else:
            raise RuntimeError(f'Invalid dialog result: {repr(result)}. Expected a {Res}.')

    def open(self):
        cancelled = self.prompt_unsaved_changes()
        if cancelled:
            return

        file_path = self.filedialog(filedialog.askopenfilename)
        if file_path is None:
            return

        self.file_path = file_path

        self.w.destroy()

        with open(file_path, 'r') as f:
            self.data = dataclass_json.load(RentManagerState, f)

        self.view = self.data.view()
        self.view.change_listeners.add(self.on_change)
        self.view.editing = True
        self.w = self.view(self._frame)
        self.w.grid(sticky='NESW')

        self.changed = False

    def new(self):
        cancelled = self.prompt_unsaved_changes()
        if cancelled:
            return

        self.w.destroy()

        self.data = RentManagerState([], [])
        self.file_path: Optional[str] = None

        self.view = self.data.view()
        self.view.change_listeners.add(self.on_change)
        self.view.editing = True
        self.w = self.view(self._frame)
        self.w.grid(sticky='NESW')

        self.changed = False

    def undo(self):
        print('undo')

    def redo(self):
        print('redo')

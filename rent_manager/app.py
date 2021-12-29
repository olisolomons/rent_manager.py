import dataclasses
import sys
from pathlib import Path
from typing import Callable, Optional
import enum

import tkinter as tk
from tkinter import filedialog
from tkinter import simpledialog

import dataclass_json
import tk_utils
from traits.core import ViewWrapper
from traits.undo_manager import UndoManager
from traits.dialog import data_dialog
from . import config
from .menu import DocumentManager, BasicEditorMenu
from .state.rent_arrangement_data import RentArrangementData

from .state.rent_manager_state import RentManagerState, RentCalculations

from tk_utils import ResettableTimer


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

        self.file_path: Optional[str] = None

        self.changed = False

        # noinspection PyTypeChecker
        self.view: ViewWrapper = None
        # noinspection PyTypeChecker
        self.w: tk.Widget = None
        # noinspection PyTypeChecker
        self.undo_manager: UndoManager = None
        # noinspection PyTypeChecker
        self.data: RentManagerState = None

        self.calculation_timer: ResettableTimer = ResettableTimer(parent, 1.5, self.do_calculations)
        self.calculation_results: Optional[RentCalculations] = None
        # noinspection PyTypeChecker
        self.notify_calculations_change: Callable[[RentCalculations], None] = None

        self.populate_from_data(RentManagerState())

        self.bind_key(self.save)
        self.bind_key(self.save_as, shift=True)
        self.bind_key(self.new)
        self.bind_key(self.open)
        self.bind_key(self.undo, key='z')
        self.bind_key(self.redo, key='y')
        self.bind_key(self.redo, key='z', shift=True)

        self._config = config.load()

        rent_manager_self = self

        class RentManagerMenu(BasicEditorMenu):
            def __init__(self, parent):
                super().__init__(parent, rent_manager_self)

                self.edit.add_command(label='Edit rent arrangements', command=rent_manager_self.edit_rent_arrangements)

        self.menu = RentManagerMenu

    def populate_from_data(self, data: RentManagerState):
        self.changed = False
        self.data = data

        self.view = data.rent_manager_main_state.view(editing=True)

        def set_on_calculations_change(on_calculations_change):
            self.notify_calculations_change = on_calculations_change

        self.w = self.view(
            self._frame,
            set_on_calculations_change=set_on_calculations_change
        )

        self.view.change_listeners.add(self.on_change)

        self.w.grid(sticky=tk_utils.STICKY_ALL)

        self.undo_manager = UndoManager.from_wrapper(self.view)

        self.calculation_timer.cancel()
        self.do_calculations()

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

    def on_change(self, _action):
        self.changed = True

        self.calculation_timer.touch()

    def do_calculations(self):
        data = self.view.get_state()
        if data is not None:
            self.data.rent_manager_main_state = data
            self.calculation_results = RentCalculations.from_rent_manager_state(self.data)
            self.notify_calculations_change(self.calculation_results)

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

    def get_save_state(self):
        view_state = self.view.get_state()
        if view_state is None:
            simpledialog.messagebox.showerror('Cannot save',
                                              'Please finish entering all data before saving the document')
        return view_state

    def save(self, state=None):
        if state is None:
            state = self.get_save_state()
        if state is None:
            return
        if self.file_path is None:
            self.save_as(state)
        else:
            state = dataclasses.replace(self.data, rent_manager_main_state=state)
            with open(self.file_path, 'w') as f:
                dataclass_json.dump(state, f)
            self.changed = False

    def save_as(self, state=None):
        if state is None:
            state = self.get_save_state()
        if state is None:
            return
        file_path = self.filedialog(filedialog.asksaveasfilename)
        if file_path is not None:
            self.file_path = file_path
            self.save(state)

    def prompt_unsaved_changes(self):
        if not self.changed:
            return False

        result = unsaved_changes_dialog(self.frame.winfo_toplevel())
        # noinspection PyPep8Naming
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

        self.calculation_timer.cancel()

        self.w.destroy()

        with open(file_path, 'r') as f:
            data = dataclass_json.load(RentManagerState, f)
            self.populate_from_data(data)

    def new(self):
        cancelled = self.prompt_unsaved_changes()
        if cancelled:
            return

        rent_arrangements = self.rent_arrangements_dialog(RentArrangementData(), 'Rent Arrangements for New Document')
        if rent_arrangements is None:
            return

        self.calculation_timer.cancel()

        self.w.destroy()

        self.populate_from_data(RentManagerState(rent_arrangement_data=rent_arrangements))

        self.file_path: Optional[str] = None

    def undo(self):
        self.undo_manager.undo()
        # self.on_change(None)

    def redo(self):
        self.undo_manager.redo()

    def edit_rent_arrangements(self):
        new_rent_arrangement_data = data_dialog(self._frame, self.data.rent_arrangement_data, 'Edit Rent Arrangements')
        if new_rent_arrangement_data is not None:
            self.data.rent_arrangement_data = new_rent_arrangement_data
            self.on_change(None)

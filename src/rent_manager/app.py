import dataclasses
import enum
import logging
import sys
import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import filedialog
from tkinter import messagebox
from tkinter import simpledialog
from typing import Callable, Optional, TYPE_CHECKING

import dataclass_json
import report_generator
import tk_utils
from tk_utils import ResettableTimer
from traits.core import ViewWrapper
from traits.dialog import data_dialog
from traits.undo_manager import UndoManager
from . import config, updater, license_
from .collate_and_export import export_collated_transactions
from .menu import DocumentManager, BasicEditorMenu
from .state.rent_arrangement_data import RentArrangementData
from .state.rent_calculations import RentCalculations
from .state.rent_manager_state import RentManagerState

if TYPE_CHECKING:
    import simple_ipc


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
    def __init__(self, parent, *, launcher_client: 'Optional[simple_ipc.Client]' = None) -> None:
        self._frame = tk.Frame(parent)

        self.launcher_client = launcher_client
        self._frame.grid_columnconfigure(0, weight=1)
        self._frame.grid_rowconfigure(0, weight=1)

        self._file_path: Optional[str] = None

        self.changed = False

        # noinspection PyTypeChecker
        self.view: ViewWrapper = None
        # noinspection PyTypeChecker
        self.view_widget: tk.Widget = None
        # noinspection PyTypeChecker
        self.undo_manager: UndoManager = None
        # noinspection PyTypeChecker
        self.data: RentManagerState = None

        self.calculation_timer: ResettableTimer = ResettableTimer(parent, 0.5, self.do_calculations)
        self.calculation_results: Optional[RentCalculations] = None
        # noinspection PyTypeChecker
        self.notify_calculations_change: Callable[[RentCalculations], None] = None
        # noinspection PyTypeChecker
        self.notify_arrangement_data_change: Callable[[RentArrangementData], None] = None

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

                self.version = tk.Menu(self, tearoff=False)
                self.add_cascade(label='Version', menu=self.version)

                version_label = rent_manager_self.get_version()
                self.version.add_command(label=version_label or 'Unknown version')
                self.version.add_command(label='Check for updates', command=rent_manager_self.check_for_updates)
                if rent_manager_self.launcher_client is None:
                    self.version.entryconfigure(1, state=tk.DISABLED)

                self.reports = tk.Menu(self, tearoff=False)
                self.add_cascade(label='Reports', menu=self.reports)

                self.reports.add_command(label='Generate report', command=rent_manager_self.generate_report)
                self.reports.add_command(label='Export multiple files\' transactions CSV',
                                         command=rent_manager_self.export_collated_transactions)

                license_menu = tk.Menu(self, tearoff=False)
                self.add_cascade(label='License', menu=license_menu)

                license_menu.add_command(label='View License', command=lambda: license_.popup(parent))

        self.menu = RentManagerMenu

        self.file_path_change_listeners: set[Callable[[str], None]] = set()

        self.frame.after_idle(self.check_license_accepted)

    def populate_from_data(self, data: RentManagerState):
        self.changed = False
        self.data = data

        self.view = data.rent_manager_main_state.view(editing=True)

        def set_on_calculations_change(on_calculations_change):
            self.notify_calculations_change = on_calculations_change

        def set_on_arrangement_data_change(on_arrangement_data_change):
            self.notify_arrangement_data_change = on_arrangement_data_change

        self.view_widget = self.view(
            self._frame,
            set_on_calculations_change=set_on_calculations_change,
            set_on_arrangement_data_change=set_on_arrangement_data_change
        )

        self.view.change_listeners.add(self.on_change)

        self.view_widget.grid(sticky=tk_utils.STICKY_ALL)

        self.undo_manager = UndoManager.from_wrapper(self.view)

        self.calculation_timer.cancel()
        self.do_calculations()

        self.notify_arrangement_data_change(self.data.rent_arrangement_data)

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, new_config):
        self._config = new_config
        config.save(self._config)

    @property
    def file_path(self) -> Optional[str]:
        return self._file_path

    @file_path.setter
    def file_path(self, value):
        self._file_path = value
        for change_listener in self.file_path_change_listeners:
            change_listener(value)

    def bind_key(self, func: Callable[[], None], key: Optional[str] = None, shift: bool = False):
        ctrl = 'Command' if sys.platform == 'darwin' else 'Control'
        if key is None:
            key = func.__name__[0]
        if shift:
            key = key.upper()
        sequence = f'<{ctrl}-{key}>'
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

    def filedialog(self, dialog, filetypes=(('RentManager File', '*.rman'),), modify_config_dir=True, parent=None,
                   **kwargs):
        if parent is None:
            parent = self.frame.winfo_toplevel()

        initial_dir = str(Path.home())
        if self.config.file_chooser_dir is not None:
            initial_dir = self.config.file_chooser_dir

        res = dialog(parent=parent, initialdir=initial_dir, filetypes=filetypes, **kwargs)

        if res and modify_config_dir:
            self.config = dataclasses.replace(self.config, file_chooser_dir=str(Path(res).parent))

        if res:
            return res
        else:
            return None

    def get_save_state(self):
        view_state = self.view.get_state()
        if view_state is None:
            messagebox.showerror('Cannot save',
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
            self.file_path = str(Path(file_path).with_suffix('.rman'))
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

        self.open_path(file_path)

    def open_path(self, file_path):
        with open(file_path, 'r') as f:
            data = dataclass_json.load(RentManagerState, f)
        self.file_path = file_path
        self.calculation_timer.cancel()
        self.view_widget.destroy()

        self.populate_from_data(data)

    def new(self):
        cancelled = self.prompt_unsaved_changes()
        if cancelled:
            return

        rent_arrangements = data_dialog(self._frame, RentArrangementData(), 'Rent Arrangements for New Document')
        if rent_arrangements is None:
            return

        self.calculation_timer.cancel()

        self.view_widget.destroy()

        self.populate_from_data(RentManagerState(rent_arrangement_data=rent_arrangements))

        self.file_path: Optional[str] = None

    def undo(self):
        self.undo_manager.undo()
        self.on_change(None)

    def redo(self):
        self.undo_manager.redo()
        self.on_change(None)

    def edit_rent_arrangements(self):
        new_rent_arrangement_data = data_dialog(self._frame, self.data.rent_arrangement_data, 'Edit Rent Arrangements')
        if new_rent_arrangement_data is not None:
            self.data.rent_arrangement_data = new_rent_arrangement_data
            self.notify_arrangement_data_change(new_rent_arrangement_data)
            self.on_change(None)

    def check_for_updates(self):
        updater.check_for_updates(self._frame, self.launcher_client, self.get_version())

    @staticmethod
    def get_version():
        parts = Path(__file__).parts
        try:
            releases_index = parts.index('releases')
        except ValueError:
            return None

        return parts[releases_index + 1]

    def generate_report(self):
        if self.file_path is None:
            filename = 'Report'
        else:
            filename = Path(self.file_path).stem

        date_format = '%d%b%Y'
        filename = f'{filename} {date.today().strftime(date_format)}'
        res = self.filedialog(filedialog.asksaveasfilename, filetypes=[('PDF', '*.pdf')], modify_config_dir=False,
                              initialfile=filename)
        if not res:
            return

        export_path = Path(res).with_suffix('.pdf')

        logging.info(f'Generating report at {export_path}')

        report_generator.generate_report(self.data, self.calculation_results, export_path)

    def export_collated_transactions(self):
        export_collated_transactions(self.frame.winfo_toplevel(), self)

    def check_license_accepted(self):
        if not self.config.accepted_license:
            accepted = license_.popup(self.frame, agree_option=True)
            if accepted:
                self.config = dataclasses.replace(self.config, accepted_license=True)
            else:
                self.frame.winfo_toplevel().destroy()

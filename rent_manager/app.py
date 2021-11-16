import sys
from typing import Callable, Optional
import tkinter as tk

import dataclass_json
from .menu import DocumentManager

from .state.rent_manager_state import RentManagerState


class RentManagerApp(DocumentManager):
    def __init__(self, parent) -> None:
        self._frame = tk.Frame(parent)

        self._frame.grid_columnconfigure(0, weight=1)
        self._frame.grid_rowconfigure(0, weight=1)

        self.data = RentManagerState([], [])

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
        print(new_state)

    def save(self):
        print('save')
        state = self.view.get_state()
        print(f'{state=}')
        with open('test.json', 'w') as f:
            dataclass_json.dump(state, f)

    def save_as(self):
        print('save_as')

    def open(self):
        print('open')
        self.w.destroy()

        with open('test.json', 'r') as f:
            self.data = dataclass_json.load(RentManagerState, f)

        self.view = self.data.view()
        self.view.change_listeners.add(self.on_change)
        self.view.editing = True
        self.w = self.view(self._frame)
        self.w.grid(sticky='NESW')

    def new(self):
        print('new')

    def undo(self):
        print('undo')

    def redo(self):
        print('redo')

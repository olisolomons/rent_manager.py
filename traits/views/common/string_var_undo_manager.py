from abc import abstractmethod
from dataclasses import dataclass
from typing import TypeVar, Generic, Optional

from traits.core import EditableView, Action
import tkinter as tk


@dataclass
class StringChangeAction(Action):
    new_state: str
    old_state: str

    new_cursor: int
    old_cursor: int

    def do(self, view: 'StringEditableView'):
        if view.string_var.get() != self.new_state:
            view.undo_manager.set(self.new_state, self.new_cursor)

    def undo(self, view: 'StringEditableView'):
        view.undo_manager.set(self.old_state, self.old_cursor)

    def stack(self, other: 'StringChangeAction') -> 'Optional[StringChangeAction]':
        return StringChangeAction(
            other.new_state, self.old_state,
            other.new_cursor, self.old_cursor
        )


@dataclass
class StringVarUndoManager:
    str_view: 'StringEditableView'

    modifying: bool = False

    previous_value: str = None
    previous_cursor: int = 0

    def __post_init__(self):
        self.str_view.entry.bind('<FocusIn>', self.on_focus)
        self.str_view.string_var.trace('w', lambda *args: self.str_view.entry.after(5, self.on_change))
        self.previous_value = self.str_view.string_var.get()

    def on_focus(self, _e):
        self.previous_cursor = self.str_view.entry.index(tk.INSERT)

    def on_change(self):
        if not self.modifying and self.str_view.string_var.get() != self.previous_value:
            cursor = self.str_view.entry.index(tk.INSERT)
            self.str_view.action(StringChangeAction(
                self.str_view.string_var.get(), self.previous_value,
                cursor, self.previous_cursor
            ))
            self.previous_value = self.str_view.string_var.get()
            self.previous_cursor = cursor

    def set(self, value, cursor):
        self.modifying = True
        self.str_view.string_var.set(value)
        self.modifying = False
        self.previous_value = value

        self.str_view.entry.icursor(cursor)
        self.previous_cursor = cursor
        self.str_view.entry.focus_set()


T = TypeVar('T')
Act = TypeVar('Act')


class StringEditableView(Generic[T], EditableView[T, StringChangeAction]):
    def __init__(self):
        super().__init__()
        # noinspection PyTypeChecker
        self.undo_manager: StringVarUndoManager = None

    def setup(self):
        self.undo_manager = StringVarUndoManager(self)

    @property
    @abstractmethod
    def string_var(self) -> tk.StringVar:
        pass

    @property
    @abstractmethod
    def entry(self) -> tk.Entry:
        pass

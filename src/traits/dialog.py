import tkinter as tk
from tkinter import simpledialog
from typing import TypeVar, Callable

from traits.core import ViewWrapper, ViewableRecord

T = TypeVar('T')


def data_dialog(root: tk.Misc, data: T, title: str, view_func: Callable[[T], ViewWrapper] = None) -> T:
    if view_func is None and isinstance(data, ViewableRecord):
        def view_func(data: ViewableRecord) -> ViewWrapper:
            return data.view(editing=True)

    class EditDataDialog(simpledialog.Dialog):
        def __init__(self):
            # noinspection PyTypeChecker
            self.view: ViewWrapper = None
            # noinspection PyTypeChecker
            self.button: tk.Button = None
            self.ok_pressed = False
            super().__init__(root, title)

        def on_change(self, _action):
            if self.view.get_state() is None:
                self.button.config(state=tk.DISABLED)
            else:
                self.button.config(state=tk.NORMAL)

        def body(self, master):
            self.view = view_func(data)
            w = self.view(master)
            w.pack(fill=tk.BOTH)

        def buttonbox(self):
            box = tk.Frame(self)

            self.button = tk.Button(box, text="Ok", command=self.ok)
            self.button.pack(side=tk.LEFT, padx=5, pady=5)
            w = tk.Button(box, text="Cancel", command=self.cancel)
            w.pack(side=tk.LEFT, padx=5, pady=5)

            self.bind("<Return>", self.ok)
            self.bind("<Escape>", self.cancel)

            self.view.change_listeners.add(self.on_change)

            box.pack()

        def validate(self):
            return self.view.get_state() is not None

        def apply(self):
            self.ok_pressed = True

        def get_state(self):
            if self.ok_pressed:
                return self.view.get_state()

    return EditDataDialog().get_state()

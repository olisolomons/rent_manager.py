from dataclasses import dataclass

from traits.core import EditableView
import tkinter as tk


@dataclass
class StringView(EditableView[str]):
    data: str

    def view(self, parent):
        return tk.Label(parent, text=self.data)

    def edit(self, parent):
        string_var = tk.StringVar(value=self.data)
        entry = tk.Entry(parent, textvariable=string_var)

        def get():
            return string_var.get()

        string_var.trace('w', lambda *args: self.notify_changed())

        return entry, get

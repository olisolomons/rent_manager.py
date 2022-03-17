import re
import tkinter as tk
from typing import Callable


class ValidatingEntry(tk.Entry):
    def __init__(self, parent, initial_value: str, validate_function: Callable[[str], bool] = None,
                 disallowed_sequences: str = None, **kw):
        self.validate_function = validate_function
        self.disallowed_sequences = re.compile(disallowed_sequences)
        self.string_var = tk.StringVar(value=initial_value)
        self.string_var.trace('w', self.on_write)

        # noinspection SpellCheckingInspection
        kw['textvariable'] = self.string_var
        super().__init__(parent, **kw)

        self.config(borderwidth=1, highlightthickness=0, highlightbackground="red", highlightcolor="red")

        self.is_valid = True

    def on_write(self, *_args):
        self.string_var.set(self.disallowed_sequences.sub('', self.string_var.get()))
        if self.is_valid != self.validate_function(self.string_var.get()):
            self.is_valid = not self.is_valid
            self.config(highlightthickness=0 if self.is_valid else 1, borderwidth=1 if self.is_valid else 0)

    def get(self):
        if self.validate_function(self.string_var.get()):
            return self.string_var.get()

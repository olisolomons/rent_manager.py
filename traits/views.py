import re
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import tkinter as tk
from typing import TypeVar, Generic

import tk_utils
from traits.core import View, EditableView

"""
d <- data description
v <- view description (function that arranges widgets)

create widget for {d}:
    make View objects for each field
    make editable if editing
    pass to {v}
    
"""


@dataclass
class CurrencyView(EditableView):
    data: int
    currency_symbol: str = '£'

    def data_string(self):
        return f'{self.data / 100:.2f}'

    def view(self, parent):
        return tk.Label(parent, text=self.currency_symbol + self.data_string())

    def edit(self, parent):
        frame = tk.Frame(parent)
        frame.grid_columnconfigure(1, weight=1)

        currency_label = tk.Label(frame, text=self.currency_symbol)
        currency_label.grid()

        valid_pattern = re.compile(r'^(\d*\.\d\d|\d+)$')
        entry = tk_utils.ValidatingEntry(
            frame, self.data_string(),
            validate_function=lambda s: bool(valid_pattern.match(s)),
            disallowed_sequences=r'[^\d.]'
        )
        entry.grid(row=0, column=1, sticky='EW')

        def get():
            s = entry.get()
            if s is not None:
                return int(float(s) * 100)

        return frame, get

from dataclasses import dataclass

from traits.core import EditableView
import tkinter as tk

from tk_utils import ValidatingEntry
import re


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
        entry = ValidatingEntry(
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

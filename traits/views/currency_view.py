from dataclasses import dataclass

from traits.core import EditableView, Act, T, ViewWrapper
import tkinter as tk

from tk_utils import ValidatingEntry
import re

from traits.views.common.string_var_undo_manager import StringEditableView


class _CurrencyView(StringEditableView[int]):
    currency_symbol: str = '£'

    @staticmethod
    def data_string(data):
        return f'{data / 100:.2f}'

    @classmethod
    def view(cls, parent, data):
        return tk.Label(parent, text=cls.currency_symbol + cls.data_string(data))

    def __init__(self, parent, data):
        super().__init__()

        self.frame = tk.Frame(parent)
        self.frame.grid_columnconfigure(1, weight=1)

        currency_label = tk.Label(self.frame, text=self.currency_symbol)
        currency_label.grid()

        valid_pattern = re.compile(r'^(\d*\.\d\d|\d+)$')
        self._entry = ValidatingEntry(
            self.frame, self.data_string(data),
            validate_function=lambda s: bool(valid_pattern.match(s)),
            disallowed_sequences=r'[^\d.]'
        )
        self._entry.grid(row=0, column=1, sticky='EW')

        self.setup()


    @property
    def string_var(self) -> tk.StringVar:
        return self._entry.string_var

    @property
    def entry(self) -> tk.Entry:
        return self._entry

    @property
    def widget(self):
        return self.frame

    def get_state(self) -> int:
        s = self._entry.get()
        if s is not None:
            return int(float(s) * 100)


class CurrencyView(ViewWrapper):
    wrapping_class = _CurrencyView

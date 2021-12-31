import tkinter as tk
from typing import Callable, Optional

import tk_utils
from traits.core import ViewWrapper
from traits.views.common.string_var_undo_manager import StringEditableView


class _IntInRange(StringEditableView):
    low: int
    high: int
    pad_digits: Optional[int] = None
    _extra_validate: Optional[Callable[[str], bool]] = None

    @classmethod
    def view(cls, parent, data) -> tk.Widget:
        return tk.Label(parent, text=cls.data_string(data))

    @classmethod
    def data_string(cls, data):
        if cls.pad_digits is None:
            return int(data)
        else:
            return f'{data:0>{cls.pad_digits}}'

    def __init__(self, parent, data):
        super().__init__()

        self.data = data

        def validate(s):
            try:
                return len(s) > 0 and (self.low <= float(s) <= self.high) and self.extra_validate(s)
            except ValueError:
                return False

        self._entry = tk_utils.ValidatingEntry(
            parent, self.data_string(data),
            validate_function=validate,
            disallowed_sequences=self.disallowed_sequences()
        )
        self.setup()

    @classmethod
    def extra_validate(cls, data):
        return cls._extra_validate(data) if cls._extra_validate else True

    @staticmethod
    def disallowed_sequences():
        return r'[^\d]'

    def get_state(self):
        if self.entry.get() is not None:
            return int(self.entry.get())

    @property
    def string_var(self) -> tk.StringVar:
        return self._entry.string_var

    @property
    def entry(self) -> tk.Entry:
        return self._entry

    @property
    def widget(self):
        return self._entry


class IntInRange(ViewWrapper):
    wrapping_class = _IntInRange

    def __call__(self, parent: tk.Misc, low=float('-inf'), high=float('inf'), pad_digits=None,
                 extra_validate=None) -> tk.Widget:
        return self._call_with_kwargs(parent, {
            'low': low,
            'high': high,
            'pad_digits': pad_digits,
            '_extra_validate': extra_validate
        })

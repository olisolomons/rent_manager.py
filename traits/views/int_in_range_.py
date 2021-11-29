import tkinter as tk
from typing import Callable, Optional, Type

import tk_utils
from traits.core import ViewWrapper
from traits.views.common.string_var_undo_manager import StringEditableView


class BaseIntInRange(StringEditableView):
    low: int
    high: int
    pad_digits: Optional[int] = None

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
        self.extra_validate: Optional[Callable[[str], bool]] = None

        def validate(s):
            return len(s) > 0 and (self.low <= int(s) <= self.high) and (
                self.extra_validate(s) if self.extra_validate else True
            )

        self._entry = tk_utils.ValidatingEntry(
            parent, self.data_string(data),
            validate_function=validate,
            disallowed_sequences=r'[^\d]'
        )
        self.setup()

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


def int_in_range(low, high, pad_digits=None) -> Type[ViewWrapper]:
    _low, _high, _pad_digits = low, high, pad_digits

    class _IntInRange(BaseIntInRange):
        low = _low
        high = _high
        pad_digits = _pad_digits

    class IntInRange(ViewWrapper):
        wrapping_class = _IntInRange

    return IntInRange

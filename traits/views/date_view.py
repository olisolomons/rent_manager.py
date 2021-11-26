import typing
from dataclasses import dataclass
import tkinter as tk
from datetime import date
from typing import Callable, Optional, Protocol, Type

import tk_utils
from traits.core import EditableView, ViewableRecord, Isomorphism, iso_view, ViewWrapper
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


@dataclass
class MyDate(ViewableRecord):
    year: int
    month: int
    day: int

    def configure(self,
                  parent: tk.Frame,
                  day: int_in_range(1, 31, pad_digits=2),
                  month: int_in_range(1, 12, pad_digits=2),
                  year: int_in_range(1000, 3000)):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(2, weight=1)
        parent.grid_columnconfigure(4, weight=1)

        day_entry = day(parent)
        day_entry.grid(row=0, column=0, sticky='EW')
        tk.Label(parent, text='/').grid(row=0, column=1)
        month_entry = month(parent)
        month_entry.grid(row=0, column=2, sticky='EW')
        tk.Label(parent, text='/').grid(row=0, column=3)
        year_entry = year(parent)
        year_entry.grid(row=0, column=4, sticky='EW')

        def day_validate(day_str):
            if not (month.get_state() is None or year.get_state() is None):
                try:
                    date(year.get_state(), month.get_state(), int(day_str))
                except ValueError:
                    return False

            return True

        day.extra_validate = day_validate
        if hasattr(month_entry, 'string_var') \
                and hasattr(day_entry, 'string_var') \
                and hasattr(year_entry, 'string_var'):
            def update_day(*args):
                day_entry.string_var.set(day_entry.string_var.get())

            month_entry.string_var.trace('w', update_day)
            year_entry.string_var.trace('w', update_day)


class DateMyDateIso(Isomorphism[date, MyDate]):

    @staticmethod
    def to(d: date) -> MyDate:
        return MyDate(d.year, d.month, d.day)

    @staticmethod
    def from_(d: MyDate) -> date:
        return date(d.year, d.month, d.day)


DateView = iso_view(DateMyDateIso)

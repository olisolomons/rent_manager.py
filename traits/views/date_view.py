import typing
from dataclasses import dataclass
import tkinter as tk
from datetime import date
from typing import Callable, Optional, Protocol, Type

import tk_utils
from traits.core import EditableView, ViewableRecord, Isomorphism, iso_view


class IntInRangeProtocol(Protocol):
    extra_validate: Optional[Callable[[str], bool]]

    def __call__(self, parent) -> tk.Widget:
        pass

    def get_state(self) -> int:
        pass


def int_in_range(low, high, pad_digits=None) -> Type[IntInRangeProtocol]:
    @dataclass
    class IntInRange(EditableView):
        data: int
        extra_validate: Optional[Callable[[str], bool]] = None

        def data_string(self):
            if pad_digits is None:
                return int(self.data)
            else:
                return f'{self.data:0>{pad_digits}}'

        def view(self, parent) -> tk.Widget:
            return tk.Label(parent, text=self.data_string())

        def edit(self, parent) -> tuple[tk.Widget, Callable[[], int]]:
            def validate(s):
                return len(s) > 0 and (low <= int(s) <= high) and (
                    self.extra_validate(s) if self.extra_validate else True
                )

            entry = tk_utils.ValidatingEntry(
                parent, self.data_string(),
                validate_function=validate,
                disallowed_sequences=r'[^\d]'
            )

            def get():
                if entry.get() is not None:
                    return int(entry.get())

            return entry, get

    return typing.cast(IntInRangeProtocol, IntInRange)


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

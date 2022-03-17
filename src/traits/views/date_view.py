import tkinter as tk
from dataclasses import dataclass
from datetime import date

from traits.core import ViewableRecord, Isomorphism, iso_view
from traits.views.int_in_range import IntInRange


@dataclass
class MyDate(ViewableRecord):
    year: int
    month: int
    day: int

    def configure(self,
                  parent: tk.Frame,
                  day: IntInRange,
                  month: IntInRange,
                  year: IntInRange):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(2, weight=1)
        parent.grid_columnconfigure(4, weight=1)

        def day_validate(day_str):
            if not (month.get_state() is None or year.get_state() is None):
                try:
                    date(year.get_state(), month.get_state(), int(day_str))
                except ValueError:
                    return False

            return True

        day_entry = day(parent, 1, 31, pad_digits=2, extra_validate=day_validate)
        day_entry.grid(row=0, column=0, sticky='EW')
        tk.Label(parent, text='/').grid(row=0, column=1)
        month_entry = month(parent, 1, 12, pad_digits=2)
        month_entry.grid(row=0, column=2, sticky='EW')
        tk.Label(parent, text='/').grid(row=0, column=3)
        year_entry = year(parent, 1000, 3000)
        year_entry.grid(row=0, column=4, sticky='EW')

        if hasattr(month_entry, 'string_var') \
                and hasattr(day_entry, 'string_var') \
                and hasattr(year_entry, 'string_var'):
            def update_day(*_args):
                day_entry.string_var.set(day_entry.string_var.get())

            # month_entry.string_var.trace('w', update_day)
            # year_entry.string_var.trace('w', update_day)

            month.wrapped_view.change_listeners.add(update_day)
            year.wrapped_view.change_listeners.add(update_day)


class DateMyDateIso(Isomorphism[date, MyDate]):

    @staticmethod
    def to(d: date) -> MyDate:
        return MyDate(d.year, d.month, d.day)

    @staticmethod
    def from_(d: MyDate) -> date:
        return date(d.year, d.month, d.day)


DateView = iso_view(DateMyDateIso)

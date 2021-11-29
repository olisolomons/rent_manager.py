from dataclasses import dataclass
import tkinter as tk
from datetime import date
from traits.core import ViewableRecord, Isomorphism, iso_view
from traits.views import int_in_range


@dataclass
class MyMonth(ViewableRecord):
    year: int
    month: int

    def configure(self,
                  parent: tk.Frame,
                  month: int_in_range(1, 12, pad_digits=2),
                  year: int_in_range(1000, 3000)):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(2, weight=1)

        month_entry = month(parent)
        month_entry.grid(row=0, column=0, sticky='EW')
        tk.Label(parent, text='/').grid(row=0, column=1)
        year_entry = year(parent)
        year_entry.grid(row=0, column=2, sticky='EW')


# not actually an isomorphism, but isomorphic to a subset is close enough
class DateMyMonthIso(Isomorphism[date, MyMonth]):

    @staticmethod
    def to(d: date) -> MyMonth:
        return MyMonth(d.year, d.month)

    @staticmethod
    def from_(d: MyMonth) -> date:
        return date(d.year, d.month, 1)


MonthView = iso_view(DateMyMonthIso)

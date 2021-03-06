import tkinter as tk
from dataclasses import dataclass
from datetime import date

from traits.core import ViewableRecord, Isomorphism, iso_view
from traits.views import IntInRange


@dataclass
class MyMonth(ViewableRecord):
    year: int
    month: int

    def configure(self,
                  parent: tk.Frame,
                  month: IntInRange,
                  year: IntInRange):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(2, weight=1)

        month_entry = month(parent, 1, 12, pad_digits=2)
        month_entry.grid(row=0, column=0, sticky='EW')
        tk.Label(parent, text='/').grid(row=0, column=1)
        year_entry = year(parent, 1000, 3000)
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

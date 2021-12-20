from dataclasses import dataclass, field
from datetime import date

from traits.core import ViewableRecord
from traits.views import DateView, CurrencyView, float_in_range

import tkinter as tk


@dataclass
class RentArrangementData(ViewableRecord):
    start_date: date = field(default_factory=date.today)
    monthly_rent: int = 0
    agents_fee: float = 0

    @staticmethod
    def configure(parent: tk.Frame, start_date: DateView, monthly_rent: CurrencyView,
                  agents_fee: float_in_range(0, 100)):
        i = 0

        def row(view, label):
            nonlocal i
            label = tk.Label(parent, text=f'{label}:')
            label.grid(row=i, column=0, sticky=tk.W)
            w = view(parent)
            w.grid(row=i, column=1, sticky=tk.E + tk.W)

            i += 1

        row(start_date, 'First day of rent')
        row(monthly_rent, 'Monthly rent due')
        row(agents_fee, 'Agent\'s fee (%)')

        parent.grid_columnconfigure(1, weight=1)

import tkinter as tk
from dataclasses import dataclass
from datetime import date

from tk_utils import Spacer
from traits.header import HasHeader
from traits.views import CurrencyView, DateView, MonthView


@dataclass
class RentPayment(HasHeader):
    @staticmethod
    def header_names() -> dict[str, str]:
        return {'amount': 'Amount', 'received_on': 'Received on', 'for_month': 'For month'}

    amount: int
    received_on: date
    for_month: date

    @staticmethod
    def configure(parent: tk.Frame, amount: CurrencyView, received_on: DateView, for_month: MonthView):
        amount(parent).grid(padx=8)
        Spacer(parent).grid(row=0, column=1)
        for_month(parent).grid(row=0, column=2, padx=8)
        Spacer(parent).grid(row=0, column=3)
        received_on(parent).grid(row=0, column=4, padx=8)
        parent.grid_columnconfigure(0, weight=1, uniform='rent_payment')
        parent.grid_columnconfigure(2, weight=2, uniform='rent_payment')
        parent.grid_columnconfigure(4, weight=3, uniform='rent_payment')

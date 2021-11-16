import tkinter as tk
from dataclasses import dataclass
from datetime import date

from traits.core import ViewableRecord
from traits.views import CurrencyView, DateView


@dataclass
class RentPayment(ViewableRecord):
    amount: int
    received_on: date

    @staticmethod
    def configure(parent: tk.Frame, amount: CurrencyView, received_on: DateView):
        amount(parent).grid(padx=15)
        received_on(parent).grid(row=0, column=1)
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=3)

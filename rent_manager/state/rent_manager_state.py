import tkinter as tk
from typing import Callable
from datetime import date
from dataclasses import dataclass
from functools import partial

from traits.core import ViewableRecord
from traits.views import ListView

from .other_transaction import OtherTransaction, TransactionReason
from .rent_payment import RentPayment


def new_other_transaction(frame: tk.Frame, add: Callable[[OtherTransaction], None]) -> tk.Widget:
    buttons_frame = tk.Frame(frame)
    for i, reason in enumerate(TransactionReason):
        button = tk.Button(
            buttons_frame,
            text=f'Add {reason.name.lower()}',
            command=lambda reason=reason: add(OtherTransaction(reason, 0, '', date.today()))
        )
        button.grid(row=0, column=i, sticky='EW')
        buttons_frame.grid_columnconfigure(i, weight=1)

    return buttons_frame


RentPaymentsView = partial(ListView, add_button_widget_func=ListView.add_button(lambda: RentPayment(0, date.today())))
OtherTransactionsView = partial(ListView, add_button_widget_func=new_other_transaction)


@dataclass
class RentManagerState(ViewableRecord):
    rent_payments: list[RentPayment]
    other_transactions: list[OtherTransaction]

    @staticmethod
    def configure(parent: tk.Frame,
                  rent_payments: RentPaymentsView,
                  other_transactions: OtherTransactionsView):
        rent_payments(parent).grid(row=0, column=0, sticky='NESW')
        other_transactions(parent).grid(row=0, column=1, sticky='NESW')

        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1, uniform='rent_manager')
        parent.grid_columnconfigure(1, weight=1, uniform='rent_manager')

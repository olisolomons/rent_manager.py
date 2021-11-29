import tkinter as tk
from typing import Callable
from datetime import date
from dataclasses import dataclass, field
from functools import partial

import tk_utils
from traits.core import ViewableRecord
from traits.views import ListView, list_view

from .other_transaction import OtherTransaction, TransactionReason
from .rent_payment import RentPayment
from traits.header import header


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


RentPaymentsView = list_view(
    add_button_widget_func=ListView[RentPayment].add_button(lambda: RentPayment(0, date.today(), date.today()))
)
OtherTransactionsView = list_view(add_button_widget_func=new_other_transaction)


@dataclass
class RentManagerState(ViewableRecord):
    rent_payments: list[RentPayment] = field(default_factory=list)
    other_transactions: list[OtherTransaction] = field(default_factory=list)

    @staticmethod
    def configure(parent: tk.Frame,
                  rent_payments: RentPaymentsView,
                  other_transactions: OtherTransactionsView):
        header(parent, RentPayment).grid(row=0, column=0, sticky=tk_utils.STICKY_ALL)
        rent_payments(parent).grid(row=1, column=0, sticky=tk_utils.STICKY_ALL)
        header(parent, OtherTransaction).grid(row=0, column=1, sticky=tk_utils.STICKY_ALL)
        other_transactions(parent).grid(row=1, column=1, sticky=tk_utils.STICKY_ALL)

        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1, uniform='rent_manager')
        parent.grid_columnconfigure(1, weight=1, uniform='rent_manager')

import tkinter as tk
from typing import Callable, Type
from datetime import date
from dataclasses import dataclass, field
from functools import partial

import tk_utils
from tk_utils.horizontal_scrolled_group import HorizontalScrolledGroup
from traits.core import ViewableRecord
from traits.views import ListView, list_view

from .other_transaction import OtherTransaction, TransactionReason, other_transaction_scrolled
from .rent_payment import RentPayment
from traits.header import header


@dataclass
class OtherTransactionMaker:
    comments_scroll_group: HorizontalScrolledGroup = None
    other_transaction_class: Type[OtherTransaction] = None

    def make_buttons(self, frame: tk.Frame, add: Callable[[OtherTransaction], None]) -> tk.Widget:
        buttons_frame = tk.Frame(frame)
        self.comments_scroll_group = HorizontalScrolledGroup(buttons_frame)
        self.comments_scroll_group.scrollbar.grid(row=0, column=0, columnspan=3, sticky=tk.E + tk.W)
        for i, reason in enumerate(TransactionReason):
            button = tk.Button(
                buttons_frame,
                text=f'Add {reason.name.lower()}',
                command=lambda reason=reason: add(self.other_transaction_class(reason, 0, '', date.today()))
            )
            button.grid(row=1, column=i, sticky='EW')
            buttons_frame.grid_columnconfigure(i, weight=1)

        return buttons_frame

    def make_other_transaction_class(self):
        self.other_transaction_class = other_transaction_scrolled(self.comments_scroll_group)


RentPaymentsView = list_view(
    add_button_widget_func=ListView[RentPayment].add_button(lambda: RentPayment(0, date.today(), date.today()))
)


@dataclass
class RentManagerState(ViewableRecord):
    rent_payments: list[RentPayment] = field(default_factory=list)
    other_transactions: list[OtherTransaction] = field(default_factory=list)

    @staticmethod
    def configure(parent: tk.Frame,
                  rent_payments: RentPaymentsView,
                  other_transactions: ListView):
        other_transaction_maker = OtherTransactionMaker()

        header(parent, RentPayment).grid(row=0, column=0, sticky=tk_utils.STICKY_ALL)
        rent_payments(parent).grid(row=1, column=0, sticky=tk_utils.STICKY_ALL)
        header(parent, OtherTransaction).grid(row=0, column=1, sticky=tk_utils.STICKY_ALL)
        other_transactions.wrapping_class._add_button_widget_func = other_transaction_maker.make_buttons
        other_transactions(parent).grid(row=1, column=1, sticky=tk_utils.STICKY_ALL)
        other_transaction_maker.make_other_transaction_class()

        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1, uniform='rent_manager')
        parent.grid_columnconfigure(1, weight=1, uniform='rent_manager')

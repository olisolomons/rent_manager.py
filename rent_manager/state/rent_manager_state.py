import tkinter as tk
import typing
from typing import Callable
from datetime import date
from dataclasses import dataclass, field

import tk_utils
from tk_utils.horizontal_scrolled_group import HorizontalScrolledGroup
from traits.core import ViewableRecord, partial_record_view
from traits.views import ListView

from .rent_arrangement_data import RentArrangementData
from .other_transaction import OtherTransaction, TransactionReason, OtherTransactionView
from .rent_payment import RentPayment
from traits.header import header


@dataclass
class OtherTransactionMaker:
    comments_scroll_group: HorizontalScrolledGroup = None

    def make_buttons(self, frame: tk.Frame, add: Callable[[OtherTransaction], None]) -> tk.Widget:
        buttons_frame = tk.Frame(frame)
        self.comments_scroll_group = HorizontalScrolledGroup(buttons_frame)
        self.comments_scroll_group.scrollbar.grid(row=0, column=0, columnspan=4, sticky=tk.E + tk.W)

        def view(record_view: OtherTransactionView, parent: tk.Misc) -> tk.Widget:
            return record_view(parent, comments_scroll_group=self.comments_scroll_group)

        OtherTransactionScrolled = partial_record_view(
            OtherTransactionView,
            OtherTransaction,
            view
        )

        for i, reason in enumerate(TransactionReason):
            name = reason.readable_name().lower()

            def add_other_transaction(reason=reason):
                add(typing.cast(Callable, OtherTransactionScrolled)(reason, 0, '', date.today()))

            button = tk.Button(
                buttons_frame,
                text=f'Add {name}',
                command=add_other_transaction
            )
            button.grid(row=1, column=i, sticky='EW')
            buttons_frame.grid_columnconfigure(i, weight=1)

        return buttons_frame


@dataclass
class RentManagerMainState(ViewableRecord):
    rent_payments: list[RentPayment] = field(default_factory=list)
    other_transactions: list[OtherTransaction] = field(default_factory=list)

    @staticmethod
    def configure(parent: tk.Frame,
                  rent_payments: ListView,
                  other_transactions: ListView):
        other_transaction_maker = OtherTransactionMaker()

        header(parent, RentPayment).grid(row=0, column=0, sticky=tk_utils.STICKY_ALL)
        rent_payments(
            parent,
            add_button_widget_func=ListView[RentPayment].add_button(lambda: RentPayment(0, date.today(), date.today()))
        ).grid(row=1, column=0, sticky=tk_utils.STICKY_ALL)
        header(parent, OtherTransaction).grid(row=0, column=1, sticky=tk_utils.STICKY_ALL)
        other_transactions(
            parent,
            add_button_widget_func=other_transaction_maker.make_buttons
        ).grid(row=1, column=1, sticky=tk_utils.STICKY_ALL)
        # other_transaction_maker.make_other_transaction_class()

        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1, uniform='rent_manager')
        parent.grid_columnconfigure(1, weight=1, uniform='rent_manager')


@dataclass
class RentManagerState:
    rent_manager_main_state: RentManagerMainState = field(default_factory=RentManagerMainState)
    rent_arrangement_data: RentArrangementData = field(default_factory=RentArrangementData)


@dataclass
class RentCalculations:
    rent_for_months: list[tuple[date, int]]
    arrears: int
    unclaimed_commission: int
    balance: int

    @classmethod
    def from_rent_manager_state(cls, rent_manager_state: RentManagerState):
        start_date = rent_manager_state.rent_arrangement_data.start_date
        months_since_start = date.today().month - start_date.month + 12 * (date.today().year - start_date.year)
        if date.today().day >= start_date.day:
            months_since_start += 1
        rent_for_months = {
            date(
                start_date.year + (start_date.month + month - 1) // 12,
                (start_date.month + month - 1) % 12 + 1,
                1
            ): 0
            for month in range(months_since_start)
        }

        for rent_payment in rent_manager_state.rent_manager_main_state.rent_payments:
            try:
                rent_for_months[rent_payment.for_month] += rent_payment.amount
            except KeyError:
                print(f'{rent_payment.for_month} is not a month in the rental period')

        total_rent_received = sum(
            rent_payment.amount
            for rent_payment in rent_manager_state.rent_manager_main_state.rent_payments
        )
        total_rent_due = months_since_start * rent_manager_state.rent_arrangement_data.monthly_rent
        total_commission_due = int(total_rent_received * rent_manager_state.rent_arrangement_data.agents_fee / 100)
        claimed_commission = sum(
            transaction.amount
            for transaction in rent_manager_state.rent_manager_main_state.other_transactions
            if transaction.reason is TransactionReason.AgentFee
        )
        total_costs = sum(
            transaction.amount
            for transaction in rent_manager_state.rent_manager_main_state.other_transactions
        )

        return cls(
            rent_for_months=list(rent_for_months.items()),
            arrears=total_rent_due - total_rent_received,
            unclaimed_commission=total_commission_due - claimed_commission,
            balance=total_rent_received - total_costs
        )

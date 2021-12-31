import tkinter as tk
import typing
from typing import Callable, Optional, Iterator
from datetime import date
from dataclasses import dataclass, field

import tk_utils
from tk_utils import Spacer
from tk_utils.horizontal_scrolled_group import HorizontalScrolledGroup
from traits.core import ViewableRecord, partial_record_view, RecordView
from traits.views import ListView, CurrencyView, DateView
from traits.dialog import data_dialog

from .rent_arrangement_data import RentArrangementData
from .other_transaction import OtherTransaction, TransactionReason, OtherTransactionView
from .rent_payment import RentPayment
from traits.header import header

import itertools


@dataclass
class FillUnpaidData(ViewableRecord):
    amount: int
    received_on: date

    @staticmethod
    def configure(parent: tk.Frame, amount: CurrencyView, received_on: DateView):
        tk.Label(parent, text='Amount paid:').grid(row=0, column=0)
        amount(parent).grid(row=0, column=1, sticky=tk.E + tk.W)
        tk.Label(parent, text='Received on:').grid(row=1, column=0)
        received_on(parent).grid(row=1, column=1)


@dataclass
class RentManagerMainState(ViewableRecord):
    rent_payments: list[RentPayment] = field(default_factory=list)
    other_transactions: list[OtherTransaction] = field(default_factory=list)

    @staticmethod
    def configure(parent: tk.Frame,
                  rent_payments: ListView[RentPayment],
                  other_transactions: ListView[OtherTransaction],
                  set_on_calculations_change: 'Callable[[Callable[[RentCalculations],None]], None]',
                  set_on_arrangement_data_change: 'Callable[[Callable[[RentArrangementData],None]], None]',
                  ):
        rent_calculations: Optional[RentCalculations] = None
        rent_arrangement_data: Optional[RentArrangementData] = None

        @set_on_calculations_change
        def on_calculations_change(calculations: RentCalculations):
            nonlocal rent_calculations
            rent_calculations = calculations
            update_other_transaction_buttons()
            arrears.config(text=f'Arrears: £{rent_calculations.arrears / 100:0.2f}')

        @set_on_arrangement_data_change
        def on_arrangement_data_change(arrangement_data: RentArrangementData):
            nonlocal rent_arrangement_data
            rent_arrangement_data = arrangement_data
            update_rent_payment_buttons()
            update_other_transaction_buttons()
            print(f'{rent_arrangement_data=}')

        def update_rent_payment_buttons():
            pass

        def make_rent_payment_buttons(parent: tk.Frame, add_basic: Callable[[RentPayment], None]) -> tk.Widget:
            nonlocal update_rent_payment_buttons

            def add(amount: int, received_on: date, for_month: date) -> None:
                add_basic(RentPayment(amount, received_on, for_month))
                add_other_transaction(
                    TransactionReason.AgentFee,
                    int(amount * rent_arrangement_data.agents_fee / 100),
                    f'For month {for_month.month:0>2}/{for_month.year}',
                    received_on
                )

            frame = tk.Frame(parent)

            def add_entry():
                first_unpaid_month = next(
                    (
                        month
                        for month, amount_paid in rent_calculations.rent_for_months
                        if amount_paid == 0
                    ),
                    date.today()
                ) if rent_calculations else date.today()
                add(rent_arrangement_data.monthly_rent, date.today(), first_unpaid_month)

            add_entry_button = tk.Button(frame, text='Add', command=add_entry)
            add_entry_button.grid(row=0, column=0, sticky=tk.E + tk.W)

            def _update_rent_payment_buttons():
                add_entry_button.config(text=f'Add £{rent_arrangement_data.monthly_rent / 100:0.2f} payment')

            update_rent_payment_buttons = _update_rent_payment_buttons

            if rent_arrangement_data is not None:
                update_rent_payment_buttons()

            def fill_unpaid():
                fill_unpaid_data = FillUnpaidData(0, date.today())
                fill_unpaid_data = data_dialog(parent, fill_unpaid_data,
                                               'Fill months that have not been fully paid-for using this payment')
                if fill_unpaid_data is None:
                    return

                def future_months():
                    month, _ = rent_calculations.rent_for_months[-1]
                    while True:
                        # the month after
                        month = date(month.year + month.month // 12, month.month % 12 + 1, 1)
                        yield month, 0

                non_filled_months: Iterator[tuple[date, int]] = itertools.chain(
                    (
                        (month, amount_paid)
                        for month, amount_paid in rent_calculations.rent_for_months
                        if amount_paid < rent_arrangement_data.monthly_rent
                    ),
                    future_months()
                )
                amount_to_fill = fill_unpaid_data.amount

                monthly_rent = rent_arrangement_data.monthly_rent
                # if monthly rent is 0, instead use `amount_to_fill` as the amount to prevent an infinite loop
                if monthly_rent == 0:
                    monthly_rent = float('inf')

                while amount_to_fill > 0:
                    for_month, already_paid = next(non_filled_months)

                    to_pay_this_month = min(amount_to_fill, monthly_rent - already_paid)
                    add(to_pay_this_month, fill_unpaid_data.received_on, for_month)

                    amount_to_fill -= to_pay_this_month

            fill_unpaid_button = tk.Button(frame, text='Fill unpaid months', command=fill_unpaid)
            fill_unpaid_button.grid(row=0, column=1, sticky=tk.E + tk.W)

            frame.grid_columnconfigure(0, weight=1)
            frame.grid_columnconfigure(1, weight=1)

            return frame

        # noinspection PyTypeChecker
        add_other_transaction: Callable[[TransactionReason, int, str, date], None] = None

        def update_other_transaction_buttons():
            pass

        def make_other_transaction_buttons(frame: tk.Frame, add_basic: Callable[[OtherTransaction], None]) -> tk.Widget:
            nonlocal add_other_transaction, update_other_transaction_buttons

            def add(reason: TransactionReason, amount: int, comment: str, _date: date) -> None:
                return add_basic(typing.cast(Callable, OtherTransactionScrolled)(reason, amount, comment, _date))

            add_other_transaction = add

            buttons_frame = tk.Frame(frame)
            comments_scroll_group = HorizontalScrolledGroup(buttons_frame)
            comments_scroll_group.scrollbar.grid(row=0, column=0, columnspan=4, sticky=tk.E + tk.W)

            def view(record_view: OtherTransactionView, parent: tk.Misc) -> tk.Widget:
                return record_view(parent, comments_scroll_group=comments_scroll_group)

            OtherTransactionScrolled = partial_record_view(
                OtherTransactionView,
                OtherTransaction,
                view
            )
            buttons: dict[TransactionReason, tk.Button] = {}
            for i, reason in enumerate(TransactionReason):
                name = reason.readable_name().lower()

                def add_other_transaction_with_reason(reason=reason):
                    add(reason, 0, '', date.today())

                button = tk.Button(
                    buttons_frame,
                    text=f'Add {name}',
                    command=add_other_transaction_with_reason
                )
                button.grid(row=1, column=i, sticky='EW')
                buttons_frame.grid_columnconfigure(i, weight=1)

                buttons[reason] = button

            def update_other_transaction_buttons():
                # agent's fee button
                agent_fee_button = buttons[TransactionReason.AgentFee]
                agent_fee_button.config(
                    text=f'Claim £{rent_calculations.unclaimed_commission / 100:0.2f} commission'
                )

                def claim_commission():
                    add(TransactionReason.AgentFee, rent_calculations.unclaimed_commission, '', date.today())

                agent_fee_button.config(command=claim_commission)

                # landlord payment button
                payment_button = buttons[TransactionReason.Payment]
                payment_button.config(text=f'Pay £{rent_calculations.balance / 100:0.2f} to landlord')

                def pay_landlord():
                    add(TransactionReason.Payment, rent_calculations.balance, '', date.today())

                payment_button.config(command=pay_landlord)

            if rent_calculations is not None:
                update_other_transaction_buttons()

            return buttons_frame

        arrears = tk.Label(parent)
        arrears.grid(row=0, column=0, sticky=tk.W, columnspan=2)
        Spacer(parent, horizontal=True).grid(row=1, column=0, columnspan=2, pady=2)

        header(parent, RentPayment).grid(row=2, column=0, sticky=tk_utils.STICKY_ALL)
        rent_payments(
            parent,
            add_button_widget_func=make_rent_payment_buttons
        ).grid(row=3, column=0, sticky=tk_utils.STICKY_ALL)
        header(parent, OtherTransaction).grid(row=2, column=1, sticky=tk_utils.STICKY_ALL)
        other_transactions(
            parent,
            add_button_widget_func=make_other_transaction_buttons
        ).grid(row=3, column=1, sticky=tk_utils.STICKY_ALL)

        parent.grid_rowconfigure(3, weight=1)
        parent.grid_columnconfigure(0, weight=1, uniform='rent_manager')
        parent.grid_columnconfigure(1, weight=1, uniform='rent_manager')

    def view(self, *, editing=False) -> 'RentManagerMainStateView':
        return RentManagerMainStateView(self, editing)


class RentManagerMainStateView(RecordView):
    def __call__(self, parent: tk.Misc,
                 set_on_calculations_change: 'Callable[[Callable[[RentCalculations],None]], None]' = None,
                 set_on_arrangement_data_change: 'Callable[[Callable[[RentArrangementData],None]], None]' = None,
                 ) -> tk.Widget:
        if set_on_calculations_change is None:
            def set_on_calculations_change(_on_calculations_change):
                pass
        if set_on_arrangement_data_change is None:
            def set_on_arrangement_data_change(_on_arrangement_data_change):
                pass

        return self._call_with_kwargs(parent, {
            'set_on_calculations_change': set_on_calculations_change,
            'set_on_arrangement_data_change': set_on_arrangement_data_change
        })


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

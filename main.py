import enum
import itertools
import tkinter as tk
from functools import partial
from typing import Callable
from dataclasses import dataclass

from tk_utils import WidgetList
from datetime import date
from traits.core import ViewableRecord, EditableView
from traits.views import CurrencyView, DateView, ListView, StringView


@dataclass
class RentPayment(ViewableRecord):
    amount: int
    received_on: date

    @staticmethod
    def configure(parent: tk.Frame, amount: CurrencyView, received_on: DateView):
        amount(parent).grid()
        received_on(parent).grid(row=0, column=1)


class TransactionReason(enum.Enum):
    Cost = enum.auto()
    Adjustment = enum.auto()
    Payment = enum.auto()


@dataclass
class OtherTransaction(ViewableRecord):
    reason: TransactionReason
    amount: int
    comment: str
    _date: date

    def configure(self, parent: tk.Frame, amount: CurrencyView, comment: StringView, _date: DateView):
        editing = amount.editing
        if editing:
            parent.grid_columnconfigure(1, weight=1)
        i = 0

        def grid(name: str, widget: tk.Widget):
            label = tk.Label(parent, text=name)
            nonlocal i
            if editing:
                label.grid(row=i, column=0, sticky='W')
                widget.grid(row=i, column=1, sticky='EW')
            else:
                label.grid(row=0, column=i)
                i += 1
                widget.grid(row=0, column=i)
            i += 1

        grid('', tk.Label(parent, text=f'{self.reason.name}: '))
        grid('Amount:', amount(parent))
        grid('Date:', _date(parent))
        if self.reason != TransactionReason.Payment:
            grid('Comment:', comment(parent))


def new_rent_payment():
    def rent_payment_generator():
        count = 0
        while True:
            count += 1
            yield RentPayment(count, date.today())

    gen = rent_payment_generator()
    return lambda: next(gen)


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


@dataclass
class RentManagerState(ViewableRecord):
    rent_payments: list[RentPayment]
    other_transactions: list[OtherTransaction]

    @staticmethod
    def configure(parent: tk.Frame,
                  rent_payments: partial(ListView, add_button_widget_func=ListView.add_button(new_rent_payment())),
                  other_transactions: partial(ListView, add_button_widget_func=new_other_transaction)):
        rent_payments(parent).grid(row=0, column=0, sticky='NESW')
        other_transactions(parent).grid(row=0, column=1, sticky='NESW')

        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)


class RentManagerApp:
    def __init__(self, parent) -> None:
        self._frame = tk.Frame(parent)
        b = tk.Button(self._frame, text='Press Me!', command=self.add_row)
        b.grid(row=0, sticky='EW')

        self._frame.grid_columnconfigure(0, weight=1)

        self.widget_list = WidgetList(self._frame)
        self.widget_list.grid(row=1, sticky='NESW')
        self._frame.grid_rowconfigure(1, weight=1)

        self.count = 0

    @property
    def frame(self) -> tk.Frame:
        return self._frame

    def add_row(self):
        l = self.widget_list.add(lambda parent: tk.Label(parent, text=f'Thing {self.count}'))

        self.count += 1


class WidgetTest:
    def __init__(self, parent) -> None:
        self._frame = tk.Frame(parent)

        self._frame.grid_columnconfigure(0, weight=1)
        b = tk.Button(self._frame, text='Edit', command=self.edit)
        b.grid(row=0, sticky='EW')
        b = tk.Button(self._frame, text='Save', command=self.save)
        b.grid(row=0, column=1, sticky='EW')

        self.data = RentManagerState([], [])

        self.view = self.data.view()
        self.w = self.view(self._frame)
        self.w.grid(row=1, sticky='NESW')

    @property
    def frame(self) -> tk.Frame:
        return self._frame

    def edit(self):
        self.w.destroy()

        self.view.editing = True
        self.w = self.view(self._frame)
        self.w.grid(row=1, column=0, sticky='NESW')

    def save(self):
        print(self.view.get_state())
        if self.view.get_state():
            self.data = self.view.get_state()

            self.view = self.data.view()
            self.w.destroy()
            self.w = self.view(self._frame)
            self.w.grid(row=1, column=0, sticky='NESW')


def main() -> None:
    w, h = 800, 600

    root = tk.Tk()
    root.geometry(f'{w}x{h}')
    app = WidgetTest(root)
    # app = RentManagerApp(root)
    app.frame.pack(fill=tk.BOTH, expand=True)

    root.mainloop()


if __name__ == '__main__':
    main()

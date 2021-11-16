import abc
import enum
import tkinter as tk
from functools import partial
from typing import Callable, Optional
from dataclasses import dataclass

from datetime import date
from traits.core import ViewableRecord
from traits.views import CurrencyView, DateView, ListView, StringView

import sys


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
            nonlocal i
            label = tk.Label(parent, text=name)
            if editing:
                label.grid(row=i, column=0, sticky='W')
                widget.grid(row=i, column=1, sticky='EW')
            else:
                label.grid(row=0, column=i)
                i += 1
                widget.grid(row=0, column=i)
            i += 1

        grid('', tk.Label(parent, text=f'{self.reason.name}: '))
        grid('Amount:' if editing else '', amount(parent))
        grid('Date:', _date(parent))
        if self.reason != TransactionReason.Payment:
            grid('Comment:', comment(parent))


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


class DocumentManager(abc.ABC):
    @abc.abstractmethod
    def save(self):
        pass

    @abc.abstractmethod
    def save_as(self):
        pass

    @abc.abstractmethod
    def open(self):
        pass

    @abc.abstractmethod
    def new(self):
        pass

    @abc.abstractmethod
    def undo(self):
        pass

    @abc.abstractmethod
    def redo(self):
        pass


class RentManagerMenu(tk.Menu):
    def __init__(self, parent, document_manager: DocumentManager):
        super().__init__(parent)

        file_menu = tk.Menu(self)
        self.add_cascade(label='File', menu=file_menu)
        file_menu.add_command(label='New', command=document_manager.new)
        file_menu.add_command(label='Open', command=document_manager.open)
        file_menu.add_command(label='Save', command=document_manager.save)
        file_menu.add_command(label='Save as', command=document_manager.save_as)

        edit = tk.Menu(self)
        self.add_cascade(label='Edit', menu=edit)
        edit.add_command(label='Undo', command=document_manager.undo)
        edit.add_command(label='Redo', command=document_manager.redo)


class RentManagerApp(DocumentManager):
    def __init__(self, parent) -> None:
        self._frame = tk.Frame(parent)

        self._frame.grid_columnconfigure(0, weight=1)
        self._frame.grid_rowconfigure(0, weight=1)

        self.data = RentManagerState([], [])

        self.view = self.data.view()
        self.view.change_listeners.add(self.on_change)
        self.view.editing = True
        self.w = self.view(self._frame)
        self.w.grid(sticky='NESW')

        self.bind_key(self.save)
        self.bind_key(self.save_as, shift=True)
        self.bind_key(self.new)
        self.bind_key(self.open)
        self.bind_key(self.undo, key='z')
        self.bind_key(self.redo, key='y')
        self.bind_key(self.redo, key='z', shift=True)

    def bind_key(self, func: Callable[[], None], key: Optional[str] = None, shift: bool = False):
        ctrl = 'Meta_L' if sys.platform == 'darwin' else 'Control'
        shift_str = '-Shift' if shift else ''
        if key is None:
            key = func.__name__[0]
        if shift:
            key = key.upper()
        sequence = f'<{ctrl}{shift_str}-{key}>'
        self.frame.bind_all(sequence, lambda e: func())

    @property
    def frame(self) -> tk.Frame:
        return self._frame

    def on_change(self, new_state):
        print(new_state)

    def save(self):
        print('save')

    def save_as(self):
        print('save_as')

    def open(self):
        print('open')

    def new(self):
        print('new')

    def undo(self):
        print('undo')

    def redo(self):
        print('redo')


def main() -> None:
    w, h = 1200, 1000

    root = tk.Tk()
    root.geometry(f'{w}x{h}')
    app = RentManagerApp(root)
    app.frame.pack(fill=tk.BOTH, expand=True)

    root.config(menu=RentManagerMenu(root, app))

    root.mainloop()


if __name__ == '__main__':
    main()

import tkinter as tk
import enum
from dataclasses import dataclass
from datetime import date

from traits.core import ViewableRecord
from traits.views import CurrencyView, StringView, DateView


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

import tkinter as tk
import enum
from dataclasses import dataclass
from datetime import date
from typing import Type

from tk_utils import Spacer
from tk_utils.horizontal_scrolled_group import HorizontalScrolledGroup
from traits.core import ViewableRecord, EditableView, View, ViewWrapper
from traits.header import HasHeader
from traits.views import CurrencyView, StringView, DateView


class TransactionReason(enum.Enum):
    Cost = enum.auto()
    Adjustment = enum.auto()
    Payment = enum.auto()
    AgentFee = enum.auto()

    def readable_name(self):
        if self is TransactionReason.AgentFee:
            return 'Agent Fee'
        else:
            return self.name


class _ReasonView(View):
    @staticmethod
    def view(parent, data: TransactionReason):
        return tk.Label(parent, text=f'{data.readable_name()}')


class ReasonView(ViewWrapper):
    wrapping_class = _ReasonView


@dataclass
class OtherTransaction(HasHeader):
    @staticmethod
    def header_names() -> dict[str, str]:
        return {
            'reason': 'Reason',
            'amount': 'Amount',
            'comment': 'Comment',
            '_date': 'Date',
        }

    reason: TransactionReason
    amount: int
    comment: str
    _date: date

    @classmethod
    def configure(cls, parent: tk.Frame, amount: CurrencyView, comment: StringView,
                  _date: DateView, reason: ReasonView):
        editing = amount.editing if hasattr(amount, 'editing') else False
        if not editing:
            if hasattr(cls, 'comments_scroll_group'):
                old_comment = comment

                class FramedComment:
                    def __init__(self, parent):
                        comments_scroll_group: HorizontalScrolledGroup = cls.comments_scroll_group
                        self.item = comments_scroll_group.add_frame(parent)
                        self.item.interior.config(bg='red')
                        old_comment(self.item.interior).pack(fill=tk.BOTH, anchor=tk.N + tk.W)

                    def grid(self, **kwargs):
                        self.item.canvas.grid(**kwargs)

                comment = FramedComment

            items = [
                (reason, 2),
                (amount, 2),
                (_date, 3),
                (comment, 4),
            ]
            is_first = True
            for i, (item, weight) in enumerate(items):
                if is_first:
                    is_first = False
                else:
                    Spacer(parent).grid(row=0, column=i * 2 - 1)

                item(parent).grid(row=0, column=i * 2, **({'sticky': tk.W} if item is comment else {}))
                parent.grid_columnconfigure(i * 2, weight=weight, uniform='other_transform')

        else:
            parent.grid_columnconfigure(1, weight=1)
            i = 0

            def grid(name: str, widget: tk.Widget):
                nonlocal i
                label = tk.Label(parent, text=name)
                label.grid(row=i, column=0, sticky='W')
                widget.grid(row=i, column=1, sticky='EW')
                i += 1

            grid('', reason(parent))
            grid('Amount:' if editing else '', amount(parent))
            grid('Date:', _date(parent))
            if reason.data != TransactionReason.Payment:
                grid('Comment:', comment(parent))


def other_transaction_scrolled(scroll_group: HorizontalScrolledGroup) -> Type[OtherTransaction]:
    class OtherTransactionScrolled(OtherTransaction):
        comments_scroll_group = scroll_group

    return OtherTransactionScrolled

import enum
import tkinter as tk
from dataclasses import dataclass
from datetime import date

from tk_utils import Spacer
from tk_utils.horizontal_scrolled_group import HorizontalScrolledGroup
from traits.core import View, ViewWrapper, RecordView
from traits.header import HasHeader
from traits.views import CurrencyView, StringView, DateView


class TransactionReason(enum.Enum):
    Cost = enum.auto()
    Adjustment = enum.auto()
    AgentFee = enum.auto()
    Payment = enum.auto()

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
    reason: TransactionReason
    amount: int
    comment: str
    date_: date

    @staticmethod
    def header_names() -> dict[str, str]:
        return {
            'reason': 'Reason',
            'amount': 'Amount',
            'comment': 'Comment',
            'date_': 'Date',
        }

    @classmethod
    def configure(cls, parent: tk.Frame, amount: CurrencyView, comment: StringView,
                  date_: DateView, reason: ReasonView,
                  comments_scroll_group=None):
        editing = amount.editing if hasattr(amount, 'editing') else False
        if not editing:
            if comments_scroll_group is not None:
                old_comment = comment

                class FramedComment:
                    def __init__(self, parent):
                        self.item = comments_scroll_group.add_frame(parent)
                        self.item.interior.config(bg='red')
                        old_comment(self.item.interior).pack(fill=tk.BOTH, anchor='nw')

                    def grid(self, **kwargs):
                        self.item.canvas.grid(**kwargs)

                comment = FramedComment

            items = [
                (reason, 2),
                (amount, 2),
                (date_, 3),
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
            grid('Date:', date_(parent))
            if reason.data != TransactionReason.Payment:
                grid('Comment:', comment(parent))


class OtherTransactionView(RecordView):
    def __call__(self, parent: tk.Misc, comments_scroll_group: HorizontalScrolledGroup = None) -> tk.Widget:
        return self._call_with_kwargs(parent, {
            'comments_scroll_group': comments_scroll_group
        })

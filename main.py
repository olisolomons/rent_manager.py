import tkinter as tk
import typing
from dataclasses import dataclass
from typing import Generic, TypeVar, Callable, Optional

from tk_utils import WidgetList
from datetime import date
from traits.core import HasTraits
from traits.views import CurrencyView


@dataclass
class RentPayment(HasTraits):
    received_on: date
    amount: int

    @staticmethod
    def view(parent: tk.Frame, amount: CurrencyView):
        amount_wgt = amount(parent)

        amount_wgt.grid()


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

        b = tk.Button(self._frame, text='Edit', command=self.edit)
        b.grid(row=0, sticky='EW')
        b = tk.Button(self._frame, text='Save', command=self.save)
        b.grid(row=0, column=1, sticky='EW')

        self.cv = CurrencyView(0)
        self.w = self.cv(self._frame)
        self.w.grid(row=1, sticky='NESW')

    @property
    def frame(self) -> tk.Frame:
        return self._frame

    def edit(self):
        self.w.destroy()
        self.cv.editing = True
        self.w = self.cv(self._frame)
        self.w.grid(row=1, column=0, sticky='NESW')

    def save(self):
        print(self.cv.get_state())


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

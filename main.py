import tkinter as tk
from typing import Callable
from dataclasses import dataclass

from tk_utils import WidgetList
from datetime import date
from traits.core import ViewableRecord, EditableView
from traits.views import CurrencyView, DateView, ListView


@dataclass
class RentPayment(ViewableRecord):
    amount: int
    received_on: date

    @staticmethod
    def configure(parent: tk.Frame, amount: CurrencyView, received_on: DateView):
        amount(parent).grid()
        received_on(parent).grid(row=0, column=1)


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

        now = date.today()
        self.data = [RentPayment(100, now), RentPayment(123, now)]
        self.count = 0

        self.view = ListView(self.data, add_button_widget_func=ListView.add_button(self.add))
        self.w = self.view(self._frame)
        self.w.grid(row=1, sticky='NESW')

    def add(self):
        self.count += 1
        return RentPayment(self.count, date.today())

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

            self.view = ListView(self.data, add_button_widget_func=ListView.add_button(self.add))
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

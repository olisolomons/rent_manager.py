import tkinter as tk
from dataclasses import dataclass
from typing import TypeVar, Generic, Callable

from traits.core import EditableView, RecordView
from tk_utils import WidgetList

T = TypeVar('T')


@dataclass
class ListView(EditableView[list[T]], Generic[T]):
    data: list[T]
    new_item_func: Callable[[], T] = None
    item_view_func: Callable[[T], EditableView[T]] = RecordView
    add_button_text: str = "Add"

    def view(self, parent) -> tk.Widget:
        frame = WidgetList(parent, editable=False)

        for item in self.data:
            frame.add(self.item_view_func(item))

        return frame

    def edit(self, parent) -> tuple[tk.Widget, Callable[[], list[T]]]:
        frame = tk.Frame(parent)
        list_frame = WidgetList(frame, editable=True)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        list_frame.grid(row=0, column=0, sticky='NESW')

        def add():
            new_item = self.new_item_func()
            list_frame.add(self.item_view_func(new_item))

        if self.new_item_func:
            add_button = tk.Button(frame, text=self.add_button_text, command=add)
            add_button.grid(row=1, column=0, sticky='EW')

        for item in self.data:
            item_view = self.item_view_func(item)
            list_frame.add(item_view)

        def get():
            return [item.data for item in list_frame.iter_items()]

        return frame, get

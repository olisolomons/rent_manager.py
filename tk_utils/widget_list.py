import tkinter as tk
from tkinter import messagebox
from .vertical_scrolled_frame import VerticalScrolledFrame
from typing import Generic, TypeVar, Optional, Callable
import typing
from dataclasses import dataclass
import dataclasses

T = TypeVar('T', bound=Callable[[tk.Widget], tk.Widget])


@dataclass
class ListItemRecord(Generic[T]):
    item: T
    frame: tk.Frame
    grid_row: int
    previous_item: Optional['ListItemRecord[T]']
    next_item: Optional['ListItemRecord[T]']
    placed: bool = False

    def do_grid(self, row=None):
        if row is not None:
            self.grid_row = row

        if self.placed:
            self.frame.grid_forget()
        self.frame.grid(row=self.grid_row, sticky='EW')


class WidgetList(VerticalScrolledFrame, Generic[T]):
    def __init__(self, parent, *args, editable=False, **kw):
        super().__init__(parent, *args, **kw)

        self.dummy_first_item = ListItemRecord(
            typing.cast(T, None),
            typing.cast(tk.Frame, None),
            -1, None, None
        )
        self.dummy_last_item = dataclasses.replace(self.dummy_first_item)
        self.dummy_first_item.next_item = self.dummy_last_item
        self.dummy_last_item.previous_item = self.dummy_first_item

        self.interior.grid_columnconfigure(0, weight=1)
        self.interior.bind_all('<Motion>', self.on_motion)

        self.dragged_item: Optional[ListItemRecord[T]] = None
        self.editable = editable

        def stop_dragging(e):
            if self.dragged_item:
                self.dragged_item.frame.config(highlightthickness=0)
                self.dragged_item = None

        self.interior.bind_all('<ButtonRelease-1>', stop_dragging)

    def add(self, item_func: T):
        item_frame = tk.Frame(self.interior, borderwidth=1, highlightbackground="blue")
        if self.editable:
            item_func.editing = True
        item = item_func(item_frame)

        def place_item():
            item.grid(row=0, column=1, sticky='EW')

        place_item()
        item_frame.grid_columnconfigure(1, weight=1)

        if self.editable:
            def edit_item():
                nonlocal item, item_func

                if item_func.editing:
                    new_state = item_func.get_state()
                    if new_state is None:
                        messagebox.showerror("Error", "Please enter valid data before saving")
                    else:
                        item.destroy()
                        item_func.data = new_state
                        item_func.editing = False

                        item = item_func(item_frame)
                        place_item()

                        edit_button.config(text="Edit")
                else:
                    item.destroy()
                    item_func.editing = True
                    item = item_func(item_frame)
                    place_item()

                    edit_button.config(text="Save")

            edit_button = tk.Button(item_frame, text="Save" if self.editable else "Edit", command=edit_item)
            edit_button.grid(row=0, column=2)

            move_arrow = tk.Label(item_frame, text='↕', cursor='fleur')
            move_arrow.grid(row=0, column=0)

            def start_dragging(e):
                self.dragged_item = item_record
                item_frame.config(highlightthickness=1)

            move_arrow.bind('<ButtonPress-1>', start_dragging)

            delete_button = tk.Button(
                item_frame, text='X',
                command=lambda: self.delete_item(item_record)
            )
            delete_button.grid(row=0, column=3)

        previous_item = self.dummy_last_item.previous_item
        item_record = ListItemRecord(
            item_func, item_frame, previous_item.grid_row + 1,
            next_item=self.dummy_last_item, previous_item=previous_item
        )
        self.dummy_last_item.previous_item = item_record
        previous_item.next_item = item_record

        item_record.do_grid()

        return item

    @staticmethod
    def delete_item(node: ListItemRecord[T]):
        node.frame.destroy()
        node.next_item.previous_item = node.previous_item
        node.previous_item.next_item = node.next_item

    def on_motion(self, e):
        if self.dragged_item is None:
            return

        def item_mid_y(item: ListItemRecord[T]):
            if item is self.dummy_first_item:
                return -float('inf')
            elif item is self.dummy_last_item:
                return float('inf')
            else:
                return item.frame.winfo_rooty() + item.frame.winfo_height() / 2

        y = e.y_root
        while True:
            if y > item_mid_y(self.dragged_item.next_item):
                swap1 = self.dragged_item
            elif y < item_mid_y(self.dragged_item.previous_item):
                swap1 = self.dragged_item.previous_item
            else:
                break

            swap2 = swap1.next_item

            swap1.next_item = swap2.next_item
            swap2.previous_item = swap1.previous_item

            swap1.previous_item = swap2
            swap2.next_item = swap1

            swap1.next_item.previous_item = swap1
            swap2.previous_item.next_item = swap2

            swap1.grid_row, swap2.grid_row = swap2.grid_row, swap1.grid_row
            swap1.do_grid()
            swap2.do_grid()

    def iter_items(self) -> typing.Iterator[T]:
        node = self.dummy_first_item
        while node.next_item is not self.dummy_last_item:
            node = node.next_item

            yield node.item

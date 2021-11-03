import dataclasses
import tkinter as tk
import typing
from typing import Generic, TypeVar, Callable, Optional
from dataclasses import dataclass
from functools import partial


class VerticalScrolledFrame(tk.Frame):
    """
    Adapted from https://stackoverflow.com/questions/16188420/tkinter-scrollbar-for-frame
    """

    def __init__(self, parent, *args, **kw):
        super().__init__(parent, *args, **kw)

        # create a canvas object and a vertical scrollbar for scrolling it
        vscrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        vscrollbar.pack(fill=tk.Y, side=tk.RIGHT, expand=tk.FALSE)
        canvas = tk.Canvas(self, bd=0, highlightthickness=0,
                           yscrollcommand=vscrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.TRUE)
        vscrollbar.config(command=canvas.yview)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = tk.Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior,
                                           anchor=tk.NW)

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                canvas.config(width=interior.winfo_reqwidth())

        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())

        canvas.bind('<Configure>', _configure_canvas)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        interior.bind("<Enter>", lambda event: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        interior.bind("<Leave>", lambda event: canvas.unbind_all("<MouseWheel>"))


T = TypeVar('T', bound=tk.Widget)


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
    def __init__(self, parent, *args, **kw):
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

        def stop_dragging(e):
            if self.dragged_item:
                self.dragged_item.frame.config(highlightthickness=0)
                self.dragged_item = None

        self.interior.bind_all('<ButtonRelease-1>', stop_dragging)

    def add(self, item_func: Callable[[tk.Widget], T]):
        item_frame = tk.Frame(self.interior, borderwidth=1, highlightbackground="blue")
        item = item_func(item_frame)
        item.grid(row=0, column=0, sticky='EW')
        item_frame.grid_columnconfigure(0, weight=1)

        move_arrow = tk.Label(item_frame, text='↕', cursor='fleur')
        move_arrow.grid(row=0, column=1)

        def start_dragging(e):
            self.dragged_item = item_record
            item_frame.config(highlightthickness=1)

        move_arrow.bind('<ButtonPress-1>', start_dragging)

        delete_button = tk.Button(
            item_frame, text='X',
            command=lambda: self.delete_item(item_record)
        )
        delete_button.grid(row=0, column=2)

        previous_item = self.dummy_last_item.previous_item
        item_record = ListItemRecord(
            item, item_frame, previous_item.grid_row + 1,
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

    def iter_items(self):
        node = self.dummy_first_item
        while node.next_item is not self.dummy_last_item:
            node = node.next_item

            yield node


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


def main() -> None:
    w, h = 800, 600

    root = tk.Tk()
    root.geometry(f'{w}x{h}')
    app = RentManagerApp(root)
    app.frame.pack(fill=tk.BOTH, expand=True)

    root.mainloop()


if __name__ == '__main__':
    main()

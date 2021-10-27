import tkinter as tk
from typing import Generic, TypeVar, Callable
from dataclasses import dataclass


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
    id_num: int
    grid_row: int
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

        self._items: dict[int, ListItemRecord[T]] = {}
        self._next_id = 0
        self.interior.grid_columnconfigure(0, weight=1)

    def add(self, item_func: Callable[[tk.Widget], T]):
        item_frame = tk.Frame(self.interior)
        item = item_func(item_frame)
        item.grid(row=0, column=0, sticky='EW')

        delete_button = tk.Button(
            item_frame, text='X',
            command=lambda item_id=self._next_id: self.delete_item(item_id)
        )
        delete_button.grid(row=0, column=1)
        item_frame.grid_columnconfigure(0, weight=1)

        item_record = ListItemRecord(item, item_frame, self._next_id, self._next_id)

        self._items[self._next_id] = item_record
        item_record.do_grid()

        self._next_id += 1

        return item

    def delete_item(self, item_id):
        self._items[item_id].frame.destroy()


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

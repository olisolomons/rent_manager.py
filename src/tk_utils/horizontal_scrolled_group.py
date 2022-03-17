import dataclasses
import tkinter as tk
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class ScrolledItem:
    canvas: tk.Canvas = field(hash=False)
    interior: tk.Frame = field(hash=False)
    interior_id: Any
    bar_size: float = field(hash=False, default=1)


class HorizontalScrolledGroup:
    def __init__(self, scrollbar_parent: tk.Misc):
        # create a canvas object and a vertical scrollbar for scrolling it
        self.scrollbar = tk.Scrollbar(scrollbar_parent, orient=tk.HORIZONTAL)
        self.scrollbar.config(command=self.xview)
        self.scrollbar.set(0, 1)

        self.x_position = 0
        self.smallest_bar_size = 1
        self.smallest_bar_size_item: Optional[ScrolledItem] = None

        self.scrolled_items: set[ScrolledItem] = set()

    def xview(self, command, pos):
        pos = float(pos)
        pos = max(0., pos)
        for scrolled_item in self.scrolled_items:
            scrolled_item.canvas.xview(command, pos)

    def add_frame(self, parent):
        def _scrollbar_set(first, last):
            nonlocal scrolled_item
            first, last = float(first), float(last)
            bar_size = last - first

            new_scrolled_item = dataclasses.replace(scrolled_item, bar_size=bar_size)

            self.scrolled_items.remove(scrolled_item)
            self.scrolled_items.add(new_scrolled_item)
            if scrolled_item is self.smallest_bar_size_item:
                self.smallest_bar_size_item = new_scrolled_item
            scrolled_item = new_scrolled_item

            if bar_size < self.smallest_bar_size:
                self.smallest_bar_size = bar_size
                self.smallest_bar_size_item = scrolled_item

                self.scrollbar.set(first, last)
            elif scrolled_item is self.smallest_bar_size_item:
                self.recompute_smallest_bar(first)

        canvas = tk.Canvas(parent, bd=0, highlightthickness=0,
                           xscrollcommand=_scrollbar_set)

        # reset the view
        canvas.xview_moveto(self.x_position)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        interior = tk.Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior,
                                           anchor=tk.NW)

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(_event):
            # update the scrollbars to match the size of the inner frame
            canvas.config(scrollregion=(0, 0, interior.winfo_reqwidth(), interior.winfo_reqheight()))
            if interior.winfo_reqheight() != canvas.winfo_height():
                # update the canvas's width to fit the inner frame
                canvas.config(height=interior.winfo_reqheight())

        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(_event):
            if interior.winfo_reqheight() != canvas.winfo_height():
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, height=canvas.winfo_height())

        canvas.bind('<Configure>', _configure_canvas)

        def _on_item_destroy(_event):
            self.scrolled_items.remove(scrolled_item)
            if scrolled_item is self.smallest_bar_size_item:
                self.recompute_smallest_bar()

        canvas.bind('<Destroy>', _on_item_destroy)

        scrolled_item = ScrolledItem(canvas, interior, interior_id)
        self.scrolled_items.add(scrolled_item)

        return scrolled_item

    def recompute_smallest_bar(self, start=0.):
        smallest = min(self.scrolled_items, key=lambda scrolled_item: scrolled_item.bar_size, default=None)
        self.smallest_bar_size_item = smallest
        if smallest:
            self.smallest_bar_size = smallest.bar_size
            self.scrollbar.set(start, start + smallest.bar_size)
        else:
            self.smallest_bar_size = 1

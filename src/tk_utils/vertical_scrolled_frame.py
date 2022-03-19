import tkinter as tk


class VerticalScrolledFrame(tk.Frame):
    """
    Adapted from https://stackoverflow.com/questions/16188420/tkinter-scrollbar-for-frame
    """

    def __init__(self, parent, *args, **kw):
        super().__init__(parent, *args, **kw)

        # create a canvas object and a vertical scrollbar for scrolling it
        v_scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        v_scrollbar.pack(fill=tk.Y, side=tk.RIGHT, expand=tk.FALSE)
        canvas = tk.Canvas(self, bd=0, highlightthickness=0,
                           yscrollcommand=v_scrollbar.set)
        self.canvas = canvas
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.TRUE)
        v_scrollbar.config(command=canvas.yview)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = tk.Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior,
                                           anchor=tk.NW)

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(_event):
            # update the scrollbars to match the size of the inner frame
            canvas.config(scrollregion=(0, 0, interior.winfo_reqwidth(), interior.winfo_reqheight()))
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                canvas.config(width=interior.winfo_reqwidth())

        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(_event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())

        canvas.bind('<Configure>', _configure_canvas)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        interior.bind("<Enter>", lambda event: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        interior.bind("<Leave>", lambda event: canvas.unbind_all("<MouseWheel>"))

    def scroll_to_end(self):
        self.canvas.yview_moveto(1)

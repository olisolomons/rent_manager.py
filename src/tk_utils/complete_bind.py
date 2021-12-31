import tkinter as tk
from typing import Callable, Any

id_number = 0


def complete_bind(widget: tk.Widget, event: str, handler: Callable[[Any], Any]):
    global id_number

    tag = f'tk_utils{id_number}'

    def do_bind(w: tk.Widget):
        bindtags = w.bindtags()
        w.bindtags((() if tag in bindtags else (tag,)) + bindtags)

        for child in w.winfo_children():
            do_bind(child)

    widget.bind_class(tag, event, handler)
    do_bind(widget)

    id_number += 1

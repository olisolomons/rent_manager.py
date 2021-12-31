import tkinter as tk
from typing import Any, Callable, Optional


class Timer:
    def __init__(self, widget: tk.Misc, length: float, callback: Callable[[], Any]):
        self._callback = callback
        self._length = length
        self._widget = widget
        self._cancelled = False

    def start(self):
        self._widget.after(int(self._length * 1000), self._on_complete)

    def _on_complete(self):
        if not self._cancelled:
            self._callback()

    def cancel(self):
        self._cancelled = True


class ResettableTimer:
    def __init__(self, widget: tk.Misc, length: float, callback: Callable[[], Any]):
        self._callback = callback
        self._length = length
        self._widget = widget
        self._timer: Optional[Timer] = None

    def touch(self):
        self.cancel()

        self._timer = Timer(self._widget, self._length, self._callback)
        self._timer.start()

    def cancel(self):
        if self._timer is not None:
            self._timer.cancel()

        self._timer = None

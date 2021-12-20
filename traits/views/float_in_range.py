import tkinter as tk

from traits.core import ViewWrapper
from traits.views.int_in_range import _IntInRange


class _FloatInRange(_IntInRange):
    low: float
    high: float

    @classmethod
    def view(cls, parent, data) -> tk.Widget:
        return tk.Label(parent, text=str(data))

    def __init__(self, parent, data):
        super().__init__(parent, data)

    @staticmethod
    def disallowed_sequences():
        return r'[^\d\-.]'

    def get_state(self):
        if self.entry.get() is not None:
            return float(self.entry.get())


class FloatInRange(ViewWrapper):
    wrapping_class = _FloatInRange

    def __call__(self, parent: tk.Misc, low=float('-inf'), high=float('inf')) -> tk.Widget:
        return self._call_with_kwargs(parent, {
            'low': low,
            'high': high
        })

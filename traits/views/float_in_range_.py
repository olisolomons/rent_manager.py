import tkinter as tk
from typing import Type

from traits.core import ViewWrapper
from traits.views.int_in_range_ import BaseIntInRange


class BaseFloatInRange(BaseIntInRange):
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


def float_in_range(low, high) -> Type[ViewWrapper]:
    _low, _high = low, high

    class _FloatInRange(BaseFloatInRange):
        low = _low
        high = _high

    class FloatInRange(ViewWrapper):
        wrapping_class = _FloatInRange

    return FloatInRange

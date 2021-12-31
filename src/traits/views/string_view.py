import tkinter as tk

from traits.core import ViewWrapper
from traits.views.common.string_var_undo_manager import StringEditableView


class _StringView(StringEditableView[str]):
    @property
    def string_var(self) -> tk.StringVar:
        return self._string_var

    @property
    def entry(self) -> tk.Entry:
        return self._entry

    @staticmethod
    def view(parent, data: str):
        return tk.Label(parent, text=data)

    def __init__(self, parent, data):
        super().__init__()
        self._string_var = tk.StringVar(value=data)
        self._entry = tk.Entry(parent, textvariable=self._string_var)

        self.setup()

    def get_state(self):
        return self._string_var.get()

    @property
    def widget(self):
        return self._entry


class StringView(ViewWrapper):
    wrapping_class = _StringView

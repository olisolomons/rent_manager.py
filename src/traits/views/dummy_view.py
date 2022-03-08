from traits.core import EditableView, ViewWrapper
from typing import Generic, TypeVar

T = TypeVar('T')
Act = TypeVar('Act')


class _DummyView(Generic[T], EditableView[T, None]):
    def __init__(self, parent, data: T):
        self.data = data

    @property
    def widget(self):
        return None

    def get_state(self) -> T:
        return self.data

    @staticmethod
    def view(parent, data):
        pass


class DummyView(ViewWrapper):
    wrapping_class = _DummyView

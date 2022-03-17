from typing import Generic, TypeVar

from traits.core import EditableView, ViewWrapper

T = TypeVar('T')
Act = TypeVar('Act')


class _DummyView(Generic[T], EditableView[T, None]):
    def __init__(self, _parent, data: T):
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

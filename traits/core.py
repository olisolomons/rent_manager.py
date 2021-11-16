import dataclasses
import typing
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import tkinter as tk
from typing import TypeVar, Generic, Callable, Optional, Type
import inspect


class View(ABC):
    @abstractmethod
    def view(self, parent) -> tk.Widget:
        pass

    def __call__(self, parent) -> tk.Widget:
        return self.view(parent)


T = TypeVar('T')
U = TypeVar('U')


@dataclass
class EditableView(View, Generic[T]):
    _editing: bool = field(default=False, init=False)
    get_state: Optional[Callable[[], T]] = field(default=None, init=False)
    change_listeners: set[Callable[[T], None]] = field(default_factory=set, init=False)

    @property
    def editing(self):
        return self._editing

    @editing.setter
    def editing(self, _editing):
        self._editing = _editing
        if not _editing:
            self.get_state = None

    @abstractmethod
    def edit(self, parent) -> tuple[tk.Widget, Callable[[], T]]:
        pass

    def __call__(self, parent) -> tk.Widget:
        if self.editing:
            widget, self.get_state = self.edit(parent)

            return widget
        else:
            return self.view(parent)

    def notify_changed(self) -> None:
        new_state = self.get_state()
        if new_state:
            for change_listener in self.change_listeners:
                change_listener(new_state)


@dataclass
class ViewableRecord(ABC):
    @abstractmethod
    def configure(self, *args, **kwargs):
        pass

    def view(self) -> EditableView:
        return RecordView(self)


@dataclass
class RecordView(EditableView[T]):
    data: ViewableRecord

    def edit(self, parent) -> tuple[tk.Widget, Callable[[], T]]:
        field_views = self.make_field_views()
        for view in field_views.values():
            if hasattr(view, 'editing'):
                view = typing.cast(EditableView, view)
                view.editing = True
                view.change_listeners.add(lambda s: self.notify_changed())

        def get():
            results = {
                field: editable_view.get_state()
                for field, view in field_views.items()
                if hasattr(view, 'editing')
                for editable_view in (typing.cast(EditableView, view),)
                if editable_view.get_state
            }
            if all(result is not None for result in results.values()):
                return dataclasses.replace(self.data, **results)

        frame = tk.Frame(parent)
        self.data.configure(frame, **field_views), get
        return frame, get

    def view(self, parent) -> tk.Widget:
        field_views = self.make_field_views()

        frame = tk.Frame(parent)
        self.data.configure(frame, **field_views)
        return frame

    def make_field_views(self) -> dict[str, View]:
        sig = inspect.signature(self.data.configure)
        return {
            field: self.make_field_view(field, sig)
            for field in list(sig.parameters)[1:]
        }

    def make_field_view(self, field, sig):
        annotation = sig.parameters[field].annotation
        field_value = getattr(self.data, field)

        if annotation is EditableView:
            return field_value.view()
        else:
            return annotation(field_value)


class Isomorphism(ABC, Generic[T, U]):
    @staticmethod
    @abstractmethod
    def to(t: T) -> U:
        pass

    @staticmethod
    @abstractmethod
    def from_(u: U) -> T:
        pass


def iso_view(iso: Type[Isomorphism[T, ViewableRecord]]) -> Type[EditableView[T]]:
    class IsoView(EditableView[T]):
        def __init__(self, data):
            super().__init__()
            self.inner_view: ViewableRecord = iso.to(data)

        def edit(self, parent) -> tuple[tk.Widget, Callable[[], T]]:
            widget, get_state = self.inner_view.view().edit(parent)

            def get():
                state = get_state()
                if state is not None:
                    return iso.from_(state)

            return widget, get

        def view(self, parent) -> tk.Widget:
            return self.inner_view.view().view(parent)

    return IsoView

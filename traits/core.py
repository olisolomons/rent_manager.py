import dataclasses
import typing
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import tkinter as tk
from typing import TypeVar, Generic, Callable, Optional
import inspect


class HasTraits:
    @classmethod
    def item(cls, name):
        dataclasses.fields(cls)
        return


class View(ABC):
    @abstractmethod
    def view(self, parent) -> tk.Widget:
        pass

    def __call__(self, parent) -> tk.Widget:
        return self.view(parent)


T = TypeVar('T')


@dataclass
class EditableView(View, Generic[T]):
    _editing: bool = field(default=False, init=False)
    get_state: Optional[Callable[[], T]] = field(default=None, init=False)

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


class ViewableRecord(ABC):
    @abstractmethod
    def configure(self, *args, **kwargs) -> tk.Widget:
        pass

    def view(self):
        return RecordView(self)


@dataclass
class RecordView(EditableView[T]):
    data: ViewableRecord

    def edit(self, parent) -> tuple[tk.Widget, Callable[[], T]]:
        field_views = self.make_field_views()
        for view in field_views.values():
            if hasattr(view, 'editing'):
                view.editing = True

        def get():
            results = {
                field: typing.cast(EditableView, view).get_state()
                for field, view in field_views.items()
                if hasattr(view, 'editing')
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
            field: sig.parameters[field].annotation(getattr(self.data, field))
            for field in list(sig.parameters)[1:]
        }


@dataclass
class ViewManager(Generic[T]):
    data: T

    def view(self):
        pass

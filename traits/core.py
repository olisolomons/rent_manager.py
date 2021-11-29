import dataclasses
import typing
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import tkinter as tk
from typing import TypeVar, Generic, Callable, Optional, Type, Any
import inspect


class View(ABC):
    @staticmethod
    @abstractmethod
    def view(parent, data):
        pass


T = TypeVar('T')
U = TypeVar('U')


class Action(Generic[U], ABC):
    @abstractmethod
    def do(self, view: U):
        pass

    @abstractmethod
    def undo(self, view: U):
        pass

    def stack(self, other: 'Action') -> 'Optional[Action]':
        pass

    @classmethod
    def checked_stack(cls, a: 'Action', b: 'Action',
                      field: str,
                      func: 'Callable[[Action],Action]') -> 'Optional[Action]':
        a_inner, b_inner = getattr(a, field), getattr(b, field)
        if type(a_inner) == type(b_inner):
            stacked = a_inner.stack(b_inner)
            if stacked is not None:
                return func(stacked)


Act = TypeVar('Act', bound=Action)


@dataclass
class EditableView(Generic[T, Act], View):
    change_listeners: set[Callable[[Act], None]] = field(default_factory=set, init=False)

    def __call__(self, parent) -> tk.Widget:
        return self.widget

    @property
    @abstractmethod
    def widget(self):
        pass

    @abstractmethod
    def get_state(self) -> T:
        pass

    def action(self, action: Act):
        for change_listener in self.change_listeners:
            change_listener(action)

        action.do(self)


class ViewWrapper(Generic[T]):
    wrapping_class: Type[EditableView] = None

    def __init__(self, data: T, editing=False):
        if self.wrapping_class is None:
            raise TypeError('ViewWrapper should be initialised via a subclass with the `wrapping_class` field set')

        self.editing = editing if self.is_editable() else False
        self.data: T = data
        self.wrapped_view: Optional[EditableView[T, Any]] = None

    def __call__(self, parent: tk.Misc) -> tk.Widget:
        if self.editing:
            wrapped_constructor = typing.cast(Callable[[tk.Misc, T], EditableView], self.wrapping_class)
            self.wrapped_view = wrapped_constructor(parent, self.data)
            return self.wrapped_view.widget
        else:
            return self.wrapping_class.view(parent, self.data)

    def get_state(self) -> Optional[T]:
        if self.wrapped_view is None:
            return self.data
        else:
            return self.wrapped_view.get_state()

    @property
    def change_listeners(self) -> Optional[set[Callable[[Act], None]]]:
        if self.wrapped_view is not None:
            return self.wrapped_view.change_listeners

    @classmethod
    def is_editable(cls):
        return issubclass(cls.wrapping_class, EditableView)


@dataclass
class ViewableRecord(ABC):
    @abstractmethod
    def configure(self, *args, **kwargs):
        pass

    def view(self, *, editing=False) -> ViewWrapper:
        return RecordView(self, editing)


@dataclass
class RecordAction(Action):
    inner_action: Action
    field: str

    def do(self, view: '_RecordView'):
        self.inner_action.do(view.field_views[self.field].wrapped_view)

    def undo(self, view: '_RecordView'):
        self.inner_action.undo(view.field_views[self.field].wrapped_view)

    def stack(self, other: 'Action') -> 'Optional[Action]':
        other = typing.cast(RecordAction, other)
        if self.field == other.field:
            return self.checked_stack(self, other, 'inner_action', lambda a: RecordAction(a, self.field))


class _RecordView(EditableView[T, RecordAction]):
    @classmethod
    def view(cls, parent, data: ViewableRecord) -> tk.Widget:
        field_views = cls.make_field_views(data)

        frame = tk.Frame(parent)
        data.configure(frame, **field_views)
        return frame

    @classmethod
    def make_field_views(cls, data: ViewableRecord) -> dict[str, ViewWrapper]:
        sig = inspect.signature(data.configure)
        return {
            field: cls.make_field_view(data, field, sig)
            for field in list(sig.parameters)[1:]
        }

    @classmethod
    def make_field_view(cls, data, field, sig):
        annotation = sig.parameters[field].annotation
        field_value = getattr(data, field)

        if annotation is EditableView:
            return field_value.view()
        else:
            return annotation(field_value)

    def __init__(self, parent, data):
        super().__init__()

        self.field_views = self.make_field_views(data)
        for view in self.field_views.values():
            if view.is_editable():
                view.editing = True

        self.frame = tk.Frame(parent)
        data.configure(self.frame, **self.field_views)

        for field, view in self.field_views.items():
            if view.is_editable() and view.change_listeners is not None:
                view.change_listeners.add(lambda action, field=field: self.on_change(RecordAction(action, field)))

        self.data = data

    def get_state(self) -> T:
        results = {
            field: editable_view.get_state()
            for field, view in self.field_views.items()
            if hasattr(view, 'editing')
            for editable_view in (typing.cast(EditableView, view),)
            if editable_view.get_state
        }
        if all(result is not None for result in results.values()):
            return dataclasses.replace(self.data, **results)

    @property
    def widget(self):
        return self.frame

    def on_change(self, action: RecordAction):
        for change_listener in self.change_listeners:
            change_listener(action)


class RecordView(ViewWrapper):
    wrapping_class = _RecordView


class Isomorphism(ABC, Generic[T, U]):
    @staticmethod
    @abstractmethod
    def to(t: T) -> U:
        pass

    @staticmethod
    @abstractmethod
    def from_(u: U) -> T:
        pass


def iso_view(iso: Type[Isomorphism[T, ViewableRecord]]) -> Type[ViewWrapper]:
    @dataclass
    class IsoAction(Action):
        inner_action: Action

        def do(self, view: '_IsoView'):
            self.inner_action.do(view.inner_view.wrapped_view)

        def undo(self, view: '_IsoView'):
            self.inner_action.undo(view.inner_view.wrapped_view)

        def stack(self, other: 'IsoAction') -> 'Optional[IsoAction]':
            other = typing.cast(IsoAction, other)
            return self.checked_stack(self, other, 'inner_action', IsoAction)

    class _IsoView(EditableView[T, IsoAction]):
        def __init__(self, parent, data):
            super().__init__()
            self.data: ViewableRecord = iso.to(data)
            self.inner_view = self.data.view(editing=True)
            self._widget = self.inner_view(parent)
            self.inner_view.change_listeners.add(self.on_change)

        def on_change(self, action: Action):
            for change_listener in self.change_listeners:
                change_listener(IsoAction(action))

        @property
        def widget(self):
            return self.inner_view.wrapped_view.widget

        def get_state(self) -> T:
            state = self.inner_view.get_state()
            if state is not None:
                return iso.from_(state)

        @staticmethod
        def view(parent, data) -> tk.Widget:
            inner_view: ViewableRecord = iso.to(data)
            return inner_view.view()(parent)

    class IsoView(ViewWrapper):
        wrapping_class = _IsoView

    return IsoView

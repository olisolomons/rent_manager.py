import dataclasses
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import tkinter as tk
from typing import TypeVar, Generic, Callable, Optional


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
    editing: bool = field(default=False, init=False)
    get_state: Optional[Callable[[], T]] = field(default=None, init=False)
    data: T

    @abstractmethod
    def edit(self, parent) -> tuple[tk.Widget, Callable[[], T]]:
        pass

    def __call__(self, parent) -> tk.Widget:
        if self.editing:
            widget, self.get_state = self.edit(parent)

            return widget
        else:
            return self.view(parent)


@dataclass
class ViewManager(Generic[T]):
    data: T

    def view(self):
        pass

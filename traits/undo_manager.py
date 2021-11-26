from dataclasses import dataclass, field

from traits.core import EditableView, ViewWrapper, Action


@dataclass
class UndoManager:
    view: EditableView
    past_actions: list[Action] = field(default_factory=list)
    future_actions: list[Action] = field(default_factory=list)

    def __post_init__(self):
        self.view.change_listeners.add(self.on_change)

    def on_change(self, action):
        self.past_actions.append(action)
        self.future_actions = []

    def undo(self):
        if self.past_actions:
            action = self.past_actions.pop()
            action.undo(self.view)
            self.future_actions.append(action)

    def redo(self):
        if self.future_actions:
            action = self.future_actions.pop()
            action.do(self.view)
            self.past_actions.append(action)

    @classmethod
    def from_wrapper(cls, wrapper: ViewWrapper):
        return cls(wrapper.wrapped_view)

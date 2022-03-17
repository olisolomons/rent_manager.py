from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from traits.core import EditableView, ViewWrapper, Action


@dataclass
class UndoManager:
    view: EditableView
    past_actions: list[Action] = field(default_factory=list)
    future_actions: list[Action] = field(default_factory=list)
    last_action_time: Optional[datetime] = None

    def __post_init__(self):
        self.view.change_listeners.add(self.on_change)

    def on_change(self, action):
        if self.past_actions and datetime.now() - self.last_action_time < timedelta(seconds=5):
            previous_action = self.past_actions.pop()
            to_add = [previous_action, action]
            if type(previous_action) == type(action):
                stack = previous_action.stack(action)
                if stack is not None:
                    to_add = [stack]
            self.past_actions.extend(to_add)
        else:
            self.past_actions.append(action)
        self.last_action_time = datetime.now()
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

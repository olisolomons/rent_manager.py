import dataclasses
import tkinter as tk
import typing
from abc import ABC
from dataclasses import dataclass
from tk_utils.complete_bind import complete_bind
from tk_utils.vertical_scrolled_frame import VerticalScrolledFrame
from tkinter import messagebox
from traits.core import EditableView, ViewWrapper, Action
from typing import Generic, TypeVar, Optional, Callable, Any

T = TypeVar('T', bound=Callable[[tk.Widget], tk.Widget])


@dataclass
class ListItemRecord(Generic[T]):
    view: ViewWrapper
    frame: tk.Frame
    grid_row: int
    previous_item: Optional['ListItemRecord[T]']
    next_item: Optional['ListItemRecord[T]']
    id_: int
    item_widget: tk.Widget
    edit_button: Optional[tk.Button]
    placed: bool = False
    actions_log: list[Action] = dataclasses.field(default_factory=list)

    def do_grid(self, row=None):
        if row is not None:
            self.grid_row = row

        if self.placed:
            self.frame.grid_forget()
        self.frame.grid(row=self.grid_row, sticky='EW')


class ListChangeAction(Action, ABC):
    pass


@dataclass
class ListItemCreate(ListChangeAction):
    id_: int
    data: Any

    def do(self, view: '_ListView'):
        view.add(self.data, self.id_, editing_item=True)

    def undo(self, view: '_ListView'):
        view.delete_item(view.dummy_last_item.previous_item)


@dataclass
class ListItemDelete(ListChangeAction):
    id_: int
    original_data: T
    previous_node_id: int
    grid_row: int

    def do(self, view: '_ListView'):
        view.delete_item(view.nodes[self.id_])

    def undo(self, view: '_ListView'):
        view.add(self.original_data, id_=self.id_,
                 previous_item=view.nodes[self.previous_node_id],
                 grid_row=self.grid_row)


@dataclass
class ListItemDeleteEditing(ListItemDelete):
    actions_log: list[Action]

    def undo(self, view: '_ListView'):
        view.add(self.original_data, editing_item=True, id_=self.id_,
                 previous_item=view.nodes[self.previous_node_id],
                 grid_row=self.grid_row)
        item_record = view.nodes[self.id_]
        inner_view: EditableView = item_record.view.wrapped_view
        for item_action in self.actions_log:
            item_action.do(inner_view)
        item_record.actions_log = list(self.actions_log)


@dataclass
class ListItemInnerAction(ListChangeAction):
    id_: int
    inner_action: Action

    def do(self, view: '_ListView'):
        item_record = view.nodes[self.id_]
        view: EditableView = item_record.view.wrapped_view
        self.inner_action.do(view)

    def undo(self, view: '_ListView'):
        item_record = view.nodes[self.id_]
        view: EditableView = item_record.view.wrapped_view
        self.inner_action.undo(view)

    def stack(self, other: 'Action') -> 'Optional[Action]':
        other = typing.cast(ListItemInnerAction, other)
        if self.id_ == other.id_:
            return self.checked_stack(self, other, 'inner_action',
                                      lambda a: ListItemInnerAction(self.id_, a))


@dataclass
class ListItemSave(ListChangeAction):
    id_: int
    original_data: Any
    actions_log: list[Action]

    def do(self, view: '_ListView'):
        item_record = view.nodes[self.id_]
        item_record.item_widget.destroy()
        item_record.view.data = item_record.view.get_state()
        item_record.view.editing = False

        item_record.item_widget = item_record.view(item_record.frame)
        view.place_item(item_record.item_widget)

        item_record.edit_button.config(text="Edit")
        item_record.actions_log = []

    def undo(self, view: '_ListView'):
        item_record = view.nodes[self.id_]
        item_record.item_widget.destroy()
        item_record.view.data = self.original_data

        item_record.view.editing = True
        item_record.item_widget = item_record.view(item_record.frame)
        view.place_item(item_record.item_widget)

        item_record.edit_button.config(text="Save")

        item_view: EditableView = item_record.view.wrapped_view
        for item_action in self.actions_log:
            item_action.do(item_view)
        item_record.actions_log = list(self.actions_log)
        view.register_events(item_record)


@dataclass
class ListItemEdit(ListChangeAction):
    id_: int

    def do(self, view: '_ListView'):
        item_record = view.nodes[self.id_]

        item_record.item_widget.destroy()
        item_record.view.editing = True
        item_record.item_widget = item_record.view(item_record.frame)

        view.place_item(item_record.item_widget)

        item_record.edit_button.config(text="Save")

        view.register_events(item_record)

    def undo(self, view: '_ListView'):
        item_record = view.nodes[self.id_]

        item_record.item_widget.destroy()
        item_record.view.data = item_record.view.get_state()
        item_record.view.editing = False
        item_record.item_widget = item_record.view(item_record.frame)
        view.place_item(item_record.item_widget)

        item_record.edit_button.config(text="Edit")


@dataclass
class ListItemSwapWithBelow(ListChangeAction):
    id_: int
    below_id: int
    previous_stacked: 'Optional[ListItemSwapWithBelow]' = None
    stop_dragging: bool = False

    def do(self, view: '_ListView'):
        if self.id_ == self.below_id:
            return
        actions = []
        action = self
        while action:
            actions.append(action)
            action = action.previous_stacked

        for action in reversed(actions):
            view.swap_with_below(view.nodes[action.id_])

    def undo(self, view: '_ListView'):
        if self.id_ == self.below_id:
            return
        action = self
        while action:
            view.swap_with_below(view.nodes[action.id_].previous_item)
            action = action.previous_stacked

    def stack(self, other: 'Action') -> 'Optional[Action]':
        other = typing.cast(ListItemSwapWithBelow, other)
        if other.stop_dragging:
            return dataclasses.replace(self, stop_dragging=True)
        if not self.stop_dragging and self.items_set().intersection(other.items_set()):
            return dataclasses.replace(other, previous_stacked=self)

    def items_set(self):
        return {self.id_, self.below_id}


class _ListView(Generic[T], EditableView[list[T], ListChangeAction]):
    item_view_func: Callable[[T], ViewWrapper] = None
    add_button_widget_func: Callable[[tk.Frame, Callable[[T], None]], tk.Widget] = None

    buttons_width = 100

    @property
    def widget(self):
        return self.frame

    def get_state(self) -> Optional[list[T]]:
        item: ViewWrapper
        items = [item.get_state() for item in self.iter_items()]
        if any(item is None for item in items):
            return
        else:
            return items

    @staticmethod
    def view(parent, data):
        list_view = _ListView(parent, data, editable=False)
        return list_view.widget

    def __init__(self, parent, data: list[T], editable=True):
        super().__init__()

        # noinspection PyTypeChecker
        self.dummy_first_item = ListItemRecord(
            None, None,
            -1, None, None,
            id_=-1,
            item_widget=None,
            edit_button=None
        )
        self.dummy_last_item = dataclasses.replace(self.dummy_first_item, id_=-2)
        self.dummy_first_item.next_item = self.dummy_last_item
        self.dummy_last_item.previous_item = self.dummy_first_item

        self.next_id = 0
        self.nodes: dict[int, ListItemRecord] = {
            node.id_: node for node in
            (self.dummy_first_item, self.dummy_last_item)
        }

        self.frame = tk.Frame(parent)
        self.list_frame = VerticalScrolledFrame(self.frame)
        self.list_frame.pack(expand=True, fill=tk.BOTH)

        self.list_frame.interior.grid_columnconfigure(0, weight=1)
        self.list_frame.interior.bind_all('<Motion>', self.on_motion, add='+')

        self.add_button = None
        if self.add_button_widget_func:
            def add(new_item: T):
                self.action(ListItemCreate(self.next_id, new_item))
                self.next_id += 1

            self.add_button = type(self).add_button_widget_func(self.frame, add)
            self.add_button.pack(fill=tk.X)

        self.dragged_item: Optional[ListItemRecord[T]] = None
        self.editable = editable

        def stop_dragging(_e):
            if self.dragged_item:
                self.dragged_item.frame.config(highlightthickness=0)
                self.dragged_item = None
                self.action(ListItemSwapWithBelow(0, 0, stop_dragging=True))

        self.list_frame.interior.bind_all('<ButtonRelease-1>', stop_dragging, add='+')

        for x in data:
            self.add(x, self.next_id)
            self.next_id += 1

    @staticmethod
    def place_item(item: tk.Widget):
        item.grid(row=0, column=1, sticky='EW')

    def register_events(self, item_record: ListItemRecord):
        def on_change(action):
            item_record.actions_log.append(action)
            self.action(ListItemInnerAction(item_record.id_, action))
            if item_record.view.get_state() is None:
                item_record.edit_button.config(state=tk.DISABLED)
            else:
                item_record.edit_button.config(state=tk.NORMAL)

        item_record.view.change_listeners.add(on_change)

        complete_bind(item_record.item_widget, '<Return>', lambda e: self.edit_item(item_record))

    def edit_item(self, item_record):
        if item_record.view.editing:
            data = item_record.view.get_state()
            if data is None:
                messagebox.showerror("Error", "Please enter valid data before saving")
            else:
                self.action(ListItemSave(item_record.id_, data, list(item_record.actions_log)))
        else:
            self.action(ListItemEdit(item_record.id_))

    def add(self, data: T, id_: int, editing_item: bool = False,
            previous_item: ListItemRecord = None, grid_row: int = None):
        if self.item_view_func:
            item_func = type(self).item_view_func(data)
        else:
            item_func = data.view()

        item_frame = tk.Frame(self.list_frame.interior, borderwidth=1, highlightbackground="blue")
        if self.editable and editing_item:
            item_func.editing = True
        item = item_func(item_frame)

        self.place_item(item)
        item_frame.grid_columnconfigure(1, weight=1)

        buttons_frame = tk.Frame(item_frame)
        buttons_frame.grid(row=0, column=2)
        item_frame.grid_columnconfigure(2, minsize=self.buttons_width, weight=0)

        edit_button = None

        if self.editable:
            edit_button = tk.Button(buttons_frame, text="Save" if item_func.editing else "Edit",
                                    command=lambda: self.edit_item(item_record))
            edit_button.grid(row=0, column=0)

            move_arrow = tk.Label(item_frame, text='↕', cursor='fleur')
            move_arrow.grid(row=0, column=0)

            def start_dragging(_e):
                self.dragged_item = item_record
                item_frame.config(highlightthickness=1)

            move_arrow.bind('<ButtonPress-1>', start_dragging)

            def delete_function():
                if item_func.editing:
                    self.action(ListItemDeleteEditing(
                        item_record.id_, item_record.view.data, item_record.previous_item.id_,
                        item_record.grid_row, list(item_record.actions_log)
                    ))
                else:
                    self.action(ListItemDelete(
                        item_record.id_, item_record.view.data, item_record.previous_item.id_,
                        item_record.grid_row
                    ))

            delete_button = tk.Button(
                buttons_frame, text='X',
                command=delete_function
            )
            delete_button.grid(row=0, column=1)

        if previous_item is None:
            previous_item = self.dummy_last_item.previous_item
        if grid_row is None:
            grid_row = previous_item.grid_row + 1
        item_record = ListItemRecord(
            item_func, item_frame, grid_row,
            next_item=previous_item.next_item, previous_item=previous_item,
            id_=id_, item_widget=item, edit_button=edit_button
        )
        previous_item.next_item.previous_item = item_record
        previous_item.next_item = item_record

        item_record.do_grid()

        self.nodes[item_record.id_] = item_record

        if editing_item:
            self.register_events(item_record)

        return item

    def delete_item(self, node: ListItemRecord[T]):
        node.frame.destroy()
        node.next_item.previous_item = node.previous_item
        node.previous_item.next_item = node.next_item

        self.nodes.pop(node.id_)

    def on_motion(self, e):
        if self.dragged_item is None:
            return

        def item_mid_y(item: ListItemRecord[T]):
            if item is self.dummy_first_item:
                return -float('inf')
            elif item is self.dummy_last_item:
                return float('inf')
            else:
                return item.frame.winfo_rooty() + item.frame.winfo_height() / 2

        y = e.y_root
        while True:
            if y > item_mid_y(self.dragged_item.next_item):
                swap1 = self.dragged_item
            elif y < item_mid_y(self.dragged_item.previous_item):
                swap1 = self.dragged_item.previous_item
            else:
                break

            self.action(ListItemSwapWithBelow(swap1.id_, swap1.next_item.id_))

    @staticmethod
    def swap_with_below(node: ListItemRecord):
        swap1 = node
        swap2 = swap1.next_item

        swap1.next_item = swap2.next_item
        swap2.previous_item = swap1.previous_item

        swap1.previous_item = swap2
        swap2.next_item = swap1

        swap1.next_item.previous_item = swap1
        swap2.previous_item.next_item = swap2

        swap1.grid_row, swap2.grid_row = swap2.grid_row, swap1.grid_row
        swap1.do_grid()
        swap2.do_grid()

    def iter_items(self) -> typing.Iterator[T]:
        node = self.dummy_first_item
        while node.next_item is not self.dummy_last_item:
            node = node.next_item

            yield node.view


U = TypeVar('U')


class ListView(ViewWrapper[list[U]], Generic[U]):
    wrapping_class = _ListView

    @staticmethod
    def add_button(new_item_func: Callable[[], U], *, text: str = 'Add') \
            -> Callable[[tk.Frame, Callable[[T], None]], tk.Widget]:
        def add_button_widget_func(frame: tk.Frame, add: Callable[[T], None]) -> tk.Widget:
            return tk.Button(frame, text=text, command=lambda: add(new_item_func()))

        return add_button_widget_func

    def __call__(self, parent: tk.Misc,
                 item_view_func: Callable[[U], ViewWrapper] = None,
                 add_button_widget_func: Callable[[tk.Frame, Callable[[U], None]], tk.Widget] = None) -> tk.Widget:
        return self._call_with_kwargs(parent, {
            'item_view_func': item_view_func,
            'add_button_widget_func': add_button_widget_func
        })

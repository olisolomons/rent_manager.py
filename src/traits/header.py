import tk_utils
import tkinter as tk
import typing
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from tk_utils import Spacer
from traits.core import ViewableRecord, ViewWrapper
from traits.views import ListView
from typing import Type, Optional, Callable


class HasHeader(ViewableRecord, metaclass=ABCMeta):
    @staticmethod
    @abstractmethod
    def header_names() -> dict[str, str]:
        pass


def header(parent: tk.Frame, view_type: Type[HasHeader]) -> tk.Widget:
    frame = tk.Frame(parent)

    @dataclass
    class Detector(ViewableRecord):
        frame: Optional[tk.Frame] = None

        def configure(self, parent):
            self.frame = tk.Frame(parent, bg='blue')
            self.frame.grid(sticky=tk_utils.STICKY_ALL)
            parent.grid_columnconfigure(0, weight=1)
            parent.grid_rowconfigure(0, weight=1)

        def detect(self):
            if self.frame.winfo_rootx() == 0 or self.frame.winfo_width() == 1:
                parent.after(5, self.detect)
                return

            left_pad = self.frame.winfo_rootx() - frame.winfo_rootx()
            outer_right_pos = frame.winfo_rootx() + frame.winfo_width()
            inner_right_pos = self.frame.winfo_rootx() + self.frame.winfo_width()
            right_pad = outer_right_pos - inner_right_pos
            create(left_pad, right_pad)

    dummy_detector = Detector()
    dummy_list: ViewWrapper = ListView([dummy_detector], editing=True)

    list_widget = dummy_list.__call__(frame)
    list_widget.grid(sticky=tk_utils.STICKY_ALL)
    frame.grid_columnconfigure(0, weight=1)

    parent.after(5, dummy_detector.detect)

    def create(left_pad, right_pad):
        list_widget.destroy()

        tk.Frame(frame).grid(row=0, column=0)
        frame.grid_columnconfigure(0, minsize=left_pad, weight=0)

        header_frame = tk.Frame(frame, )
        header_frame.grid(row=0, column=1, sticky=tk_utils.STICKY_ALL)
        frame.grid_columnconfigure(1, weight=1)

        header_names = view_type.header_names()
        header_views = {attr: lambda parent, name=name: tk.Label(parent, text=name) for attr, name in
                        header_names.items()}
        view_configure = typing.cast(Callable[[tk.Frame, ...], None], view_type.configure)
        view_configure(header_frame, **header_views)

        tk.Frame(frame).grid(row=0, column=2)
        frame.grid_columnconfigure(2, minsize=right_pad, weight=0)

        Spacer(frame, horizontal=True).grid(row=1, columnspan=3)

    return frame

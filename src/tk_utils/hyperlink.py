import tkinter as tk
import webbrowser


class Hyperlink(tk.Label):
    def __init__(self, parent, url, text=None, **kwargs):
        kwargs.setdefault('fg', 'blue')
        kwargs.setdefault('cursor', 'hand2')

        if text is None:
            text = url

        super().__init__(parent, text=text, **kwargs)

        self.bind('<Button-1>', lambda _event: webbrowser.open_new_tab(url))

    @classmethod
    def mailto(cls, parent, email, text=None, **kwargs):
        if text is None:
            text = email
        return cls(parent, url=f'mailto:?to={email}', text=text, **kwargs)

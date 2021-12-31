import tkinter as tk


class Spacer:
    def __init__(self, parent, horizontal=False):
        self.horizontal = horizontal
        self.canvas = tk.Canvas(parent, width=1, height=1, bg='black')

    def grid(self, **kwargs):
        sticky = tk.E + tk.W if self.horizontal else tk.N + tk.S
        self.canvas.grid(sticky=sticky, **kwargs)

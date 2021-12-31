from abc import ABC, abstractmethod
import tkinter as tk


class DocumentManager(ABC):
    @abstractmethod
    def save(self):
        pass

    @abstractmethod
    def save_as(self):
        pass

    @abstractmethod
    def open(self):
        pass

    @abstractmethod
    def new(self):
        pass

    @abstractmethod
    def undo(self):
        pass

    @abstractmethod
    def redo(self):
        pass


class BasicEditorMenu(tk.Menu):
    def __init__(self, parent, document_manager: DocumentManager):
        super().__init__(parent)

        file_menu = self.file_menu = tk.Menu(self, tearoff=False)
        self.add_cascade(label='File', menu=file_menu)
        file_menu.add_command(label='New', command=document_manager.new)
        file_menu.add_command(label='Open', command=document_manager.open)
        file_menu.add_command(label='Save', command=document_manager.save)
        file_menu.add_command(label='Save as', command=document_manager.save_as)

        edit = self.edit = tk.Menu(self, tearoff=False)
        self.add_cascade(label='Edit', menu=edit)
        edit.add_command(label='Undo', command=document_manager.undo)
        edit.add_command(label='Redo', command=document_manager.redo)

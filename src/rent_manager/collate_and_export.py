import csv
import json
import logging
import threading
import tkinter as tk
import traceback
import typing
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Callable, Any

import dataclass_json
import tk_utils
from currency import format_currency
from rent_manager.state.all_transactions import get_all_transactions
from rent_manager.state.other_transaction import OtherTransaction
from rent_manager.state.rent_manager_state import RentManagerState
from rent_manager.state.rent_payment import RentPayment
from traits.core import ViewableRecord
from traits.views import DummyView, ListView, IntInRange


@dataclass
class RentManagerFilePath(ViewableRecord):
    path: str
    message: str
    valid: bool

    @staticmethod
    def configure(parent: tk.Frame, path: DummyView, message: DummyView, valid: DummyView):
        parent.grid_columnconfigure(0, weight=1)
        path_label = tk.Label(parent, text=path.get_state())
        path_label.grid(sticky=tk.W)

        message = tk.Label(parent, text=(message.get_state() or ''))
        message.grid(row=0, column=1)
        message.config(fg='green' if valid.get_state() else 'red')

    @classmethod
    def from_path(cls, path: str):
        try:
            with open(path, 'r') as f:
                data: RentManagerState = dataclass_json.load(RentManagerState, f)

        except FileNotFoundError:
            return cls(path, 'File does not exist', False)
        except OSError:
            return cls(path, 'Unable to read file', False)
        except json.JSONDecodeError:
            return cls(path, 'Corrupt file or invalid file type', False)
        else:
            return cls.from_data(path, data)

    @classmethod
    def from_path_callback(cls, root: tk.Misc, path: str, callback: 'Callable[[RentManagerFilePath],None]'):
        def do():
            data = cls.from_path(path)
            root.after_idle(lambda: callback(data))

        thread = threading.Thread(target=do)
        thread.start()

    @classmethod
    def from_data(cls, path, data: RentManagerState):
        month_format = '%b %Y'
        start = data.rent_arrangement_data.start_date
        rent_payment: RentPayment
        transaction: OtherTransaction
        end = max(
            max((rent_payment.received_on for rent_payment in data.rent_manager_main_state.rent_payments),
                default=start),
            max((transaction.date_ for transaction in data.rent_manager_main_state.other_transactions),
                default=start)
        )
        return cls(path, f'{start.strftime(month_format)} - {end.strftime(month_format)}', True)


def export_collated_transactions(root, rent_manager_self):
    class FilesSelectorDialog(tk.Toplevel):
        def __init__(self):
            super().__init__(root)
            self.title('Export Collated Transactions as CSV')

            self.geometry(f'{int(root.winfo_width() * 0.8)}x{int(root.winfo_height() * 0.8)}')

            initial_files = []
            if rent_manager_self.file_path is not None:
                initial_files = [rent_manager_self.file_path]

            self.tax_year_frame = tk.Frame(self)
            self.tax_year_frame.grid(row=0, column=0, columnspan=2, sticky=tk_utils.STICKY_ALL)

            self.tax_year_start = IntInRange(date.today().year - 1, editing=True)

            tax_year_end = tk.Label(self.tax_year_frame)

            def update_tax_year_end(_act=None):
                start = self.tax_year_start.get_state()
                if start is not None:
                    tax_year_end.config(text=str(self.tax_year_start.get_state() + 1))

            def tax_year():
                frame = self.tax_year_frame
                row = 0

                update_tax_year_end()

                for col, item in enumerate((
                        tk.Label(frame, text='Export only transactions between 6 Apr '),
                        self.tax_year_start(frame, 1000, 3000),
                        tk.Label(frame, text=' and 5 Apr '),
                        tax_year_end
                )):
                    item.grid(row=0, column=col)

                self.tax_year_start.change_listeners.add(update_tax_year_end)

                frame.grid_columnconfigure(row + 1)

            tax_year()

            self.files_list, self.files_list_widget = self.make_files_widget(initial_files)
            self.files_list_widget.grid(row=1, column=0, columnspan=2, sticky=tk_utils.STICKY_ALL)

            self.grid_rowconfigure(1, weight=1)
            self.grid_columnconfigure(0, weight=1)
            self.grid_columnconfigure(1, weight=1)

            export_button = tk.Button(self, text='Export', command=self.export)
            export_button.grid(row=2, column=0, sticky=tk.E + tk.W)
            cancel_button = tk.Button(self, text='Cancel', command=self.cancel)
            cancel_button.grid(row=2, column=1, sticky=tk.E + tk.W)
            self.bind('<Escape>', lambda e: self.cancel())

        def export(self):
            file_names = [file.path for file in self.files_list.get_state()]
            if not file_names:
                messagebox.showwarning('Warning', 'Please choose at least 1 file before exporting.', parent=self)
                return
            tax_year_start_year = self.tax_year_start.get_state()
            if not tax_year_start_year:
                messagebox.showwarning('Warning', 'Please enter a valid tax year', parent=self)
                return

            if len({Path(name).resolve() for name in file_names}) < len(file_names):
                messagebox.showwarning('Warning', 'The file list contains duplicates', parent=self)
                return

            tax_year_start_date = date(tax_year_start_year, 4, 5)
            tax_year_end_date = date(tax_year_start_year + 1, 4, 5)

            out_csv_filename = rent_manager_self.filedialog(
                filedialog.asksaveasfilename,
                modify_config_dir=False,
                filetypes=[('Comma Separated Values (table)', '*.csv')],
                parent=self
            )
            if not out_csv_filename:
                # user cancelled
                return

            files_data = []

            logging.info(f'Exporting collated transaction: {file_names}')
            try:
                for file in file_names:
                    with open(file, 'r') as f:
                        data = dataclass_json.load(RentManagerState, f)
                        files_data.append(data)

            except (OSError, json.JSONDecodeError):
                logging.warning(traceback.format_exc())

                messagebox.showerror(
                    'Error',
                    'There is a problem reading some of the files. Please check that they are correct',
                    parent=self
                )

                self.files_list_widget.destroy()

                self.files_list, self.files_list_widget = self.make_files_widget(file_names)
                self.files_list_widget.grid(row=1, column=0, columnspan=2, sticky=tk_utils.STICKY_ALL)
            except Exception:
                logging.warning(traceback.format_exc())
                raise
            else:
                date_format = '%d/%m/%Y'

                with open(out_csv_filename, 'w') as out_csv_file:
                    out_csv = csv.writer(out_csv_file)
                    for data in files_data:
                        for transaction in get_all_transactions(data):
                            if tax_year_start_date < transaction.date <= tax_year_end_date:
                                out_csv.writerow(
                                    [
                                        transaction.date.strftime(date_format),
                                        transaction.type,
                                        format_currency(transaction.amount),
                                        transaction.comment
                                    ]
                                )

                self.destroy()

        def cancel(self):
            self.destroy()

        @classmethod
        def add_files(cls, file_names: list[str], add: Callable, index: int = 0):
            if index >= len(file_names):
                return

            def add_then_next(result):
                add(result)
                cls.add_files(file_names, add, index + 1)

            RentManagerFilePath.from_path_callback(root, file_names[index], add_then_next)

        def make_files_widget(self, file_names):
            files_list = ListView([], editing=True)

            def add_initial(initial):
                view = typing.cast(Any, files_list.wrapped_view)
                view.add(initial, view.next_id)
                view.next_id += 1

            self.add_files(file_names, add_initial)

            files_list_widget = files_list(
                self,
                add_button_widget_func=self.make_add_file_button
            )
            return files_list, files_list_widget

        def make_add_file_button(self, parent, add):
            frame = tk.Frame(parent)

            def add_file():
                files = rent_manager_self.filedialog(
                    filedialog.askopenfilenames,
                    modify_config_dir=False, parent=self
                )
                self.add_files(files or (), add)

            add_button = tk.Button(frame, text='Add file(s)', command=add_file)
            add_button.grid(sticky=tk_utils.STICKY_ALL)

            frame.grid_rowconfigure(0, weight=1)
            frame.grid_columnconfigure(0, weight=1)

            return frame

    files_selector = FilesSelectorDialog()
    files_selector.wait_visibility()
    files_selector.grab_set()
    files_selector.wait_window(files_selector)

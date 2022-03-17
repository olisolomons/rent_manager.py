import logging
import tkinter as tk
import traceback
from pathlib import Path
from tkinter.scrolledtext import ScrolledText

import tk_utils

license_text = None
license_file = Path().resolve().parent / 'LICENSE'


def popup(root: tk.Misc, agree_option=False):
    global license_text
    if license_text is None:
        try:
            with license_file.open('r') as file:
                license_text = file.read()
        except OSError:
            logging.warning(f'Unable to open license file: {traceback.format_exc()}')
            return

    class LicensePopup(tk.Toplevel):
        def __init__(self):
            super().__init__(root)
            self.title('License')
            self.geometry(f'{int(root.winfo_width() * 0.8) or 800}x{int(root.winfo_height() * 0.8) or 400}')

            license_text_field = ScrolledText(self)
            license_text_field.insert(tk.CURRENT, license_text)
            license_text_field.grid(row=0, column=0, sticky=tk_utils.STICKY_ALL)
            license_text_field.config(state=tk.DISABLED)

            self.grid_columnconfigure(0, weight=1)
            self.grid_rowconfigure(0, weight=1)

            more_details = tk.Frame(self)
            more_details.grid(row=1, column=0, sticky=tk_utils.STICKY_ALL)
            tk.Label(more_details, text='For more license details, see: ').grid(row=0, column=0)
            tk_utils.Hyperlink(more_details, url='http://fair.io').grid(row=0, column=1)

            contact = tk.Frame(self)
            contact.grid(row=2, column=0, sticky=tk_utils.STICKY_ALL)
            tk.Label(contact, text='To obtain a license, please contact ').grid(row=0, column=0)
            tk_utils.Hyperlink.mailto(contact, 'oli.solomons@gmail.com').grid(row=0, column=1)

            buttons = tk.Frame(self)
            buttons.grid(row=3, column=0, sticky=tk_utils.STICKY_ALL, padx=20)

            buttons.grid_columnconfigure(0, weight=1)
            close = tk.Button(buttons, text='Close', command=self.destroy)
            close.grid(row=0, column=0, sticky=tk_utils.STICKY_ALL)
            if agree_option:
                buttons.grid_columnconfigure(1, weight=1)
                agree = tk.Button(buttons, text='Agree', command=self.accept)
                agree.grid(row=0, column=1, sticky=tk_utils.STICKY_ALL)
            self.accepted = False

        def accept(self):
            self.accepted = True
            self.destroy()

    license_popup = LicensePopup()
    license_popup.wait_visibility()
    license_popup.grab_set()
    license_popup.wait_window(license_popup)

    if agree_option:
        return license_popup.accepted

import tkinter as tk

from rent_manager.app import RentManagerApp
from rent_manager.menu import RentManagerMenu


def main() -> None:
    w, h = 1200, 1000

    root = tk.Tk()
    root.geometry(f'{w}x{h}')
    app = RentManagerApp(root)
    app.frame.pack(fill=tk.BOTH, expand=True)

    root.config(menu=RentManagerMenu(root, app))

    root.mainloop()


if __name__ == '__main__':
    main()

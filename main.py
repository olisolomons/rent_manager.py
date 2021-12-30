import tkinter as tk

from rent_manager.app import RentManagerApp
import report_generator

def main() -> None:
    report_generator.hello_world()
    w, h = 1200, 1000

    root = tk.Tk()
    root.geometry(f'{w}x{h}')
    root.title('Rent Manager')

    app = RentManagerApp(root)
    app.frame.pack(fill=tk.BOTH, expand=True)

    root.config(menu=app.menu(root))

    root.mainloop()


if __name__ == '__main__':
    main()

import argparse
import tkinter as tk
from pathlib import Path

import sys

import report_generator
from rent_manager.app import RentManagerApp

parser = argparse.ArgumentParser()
parser.add_argument('file', help='the file to open', nargs='?')
parser.add_argument('--port', help='port for communicating with launcher process')


def main() -> None:
    report_generator.hello_world()
    args = parser.parse_args()

    w, h = 1200, 1000

    root = tk.Tk()
    root.geometry(f'{w}x{h}')
    root.title('Rent Manager')

    def make_app_then_mainloop(launcher_socket=None):
        app = RentManagerApp(root, launcher_client=launcher_socket)
        if args.file is not None:
            app.open_path(args.file)
        app.frame.pack(fill=tk.BOTH, expand=True)

        root.config(menu=app.menu(root))

        root.mainloop()

    if args.port is not None:
        sys.path.append(str(Path(__file__).parent.parent / 'launcher'))
        import simple_ipc

        with simple_ipc.get_sock() as launcher_socket:
            launcher_client = simple_ipc.Client(launcher_socket, int(args.port))
            make_app_then_mainloop(launcher_client)
    else:
        make_app_then_mainloop()


if __name__ == '__main__':
    main()

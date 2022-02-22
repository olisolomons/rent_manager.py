import argparse
import logging
import tkinter as tk
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from PIL import Image

import sys

import report_generator
from rent_manager.app import RentManagerApp
from rent_manager.config import rent_manager_dirs

parser = argparse.ArgumentParser()
parser.add_argument('file', help='the file to open', nargs='?')
parser.add_argument('--port', help='port for communicating with launcher process')

log_dir = Path(rent_manager_dirs.user_log_dir)
log_dir.mkdir(parents=True, exist_ok=True)

handler = TimedRotatingFileHandler(filename=log_dir / 'app', when='D', backupCount=15, encoding='utf-8', delay=False)

logging.basicConfig(
    format='[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
    handlers=[handler],
    level=logging.INFO
)


def set_icon(root: tk.Tk) -> None:
    logo_png = Path(__file__).parent.parent / 'logo.png'

    if sys.platform.startswith('linux'):
        root.my_icon_photo = photo = tk.PhotoImage(file=logo_png)
        root.iconphoto(True, photo)
    else:
        icon_type = 'icns' if sys.platform.startswith('darwin') else 'ico'
        icon_sizes = [(16 << i, 16 << i) + (1,) * (icon_type == 'icns') for i in range(7)]

        logo_icon = Path(__file__).parent.parent / f'logo.{icon_type}'

        if not logo_icon.is_file():
            Image.open(logo_png).save(logo_icon, format=icon_type, sizes=icon_sizes)

        root.iconbitmap(str(logo_icon))

        if sys.platform.startswith('darwin'):
            try:
                from Cocoa import NSApplication, NSImage
            except ImportError:
                logging.warning('Unable to import pyobjc modules')
            else:
                ns_application = NSApplication.sharedApplication()
                logo_ns_image = NSImage.alloc().initByReferencingFile_(str(logo_icon.resolve()))
                ns_application.setApplicationIconImage_(logo_ns_image)


def main() -> None:
    report_generator.hello_world()
    args = parser.parse_args()

    w, h = 1200, 1000

    if sys.platform.startswith('linux'):
        root = tk.Tk(className='rent manager')
    else:
        root = tk.Tk()
    root.geometry(f'{w}x{h}')
    root.title('Rent Manager')
    set_icon(root)

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

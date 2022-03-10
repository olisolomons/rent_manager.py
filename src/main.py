import sys

import argparse
import logging
import tkinter as tk
import traceback
from PIL import Image
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
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
    handlers=[handler, logging.StreamHandler(sys.stdout)],
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

        if sys.platform.startswith('darwin'):
            def set_window_info():
                try:
                    from Cocoa import NSApplication, NSImage
                except ImportError:
                    logging.warning('Unable to import pyobjc modules')
                else:
                    logging.info('Setting MacOS icon')
                    ns_application = NSApplication.sharedApplication()
                    logo_ns_image = NSImage.alloc().initByReferencingFile_(str(logo_icon.resolve()))
                    ns_application.setApplicationIconImage_(logo_ns_image)

                    logging.info('Setting MacOS title')
                    menu = ns_application.mainMenu().itemAtIndex_(0).submenu()
                    menu.setTitle_('Rent Manager')

            root.after(1000, set_window_info)
        else:
            root.iconbitmap(str(logo_icon))


def main() -> None:
    args = parser.parse_args()

    w, h = 1200, 1000

    if sys.platform.startswith('linux'):
        root = tk.Tk(className='rent manager')
    else:
        root = tk.Tk()
    root.geometry(f'{w}x{h}')
    root.title('Rent Manager - (new document)')
    set_icon(root)

    def make_app_then_mainloop(launcher_socket=None):
        app = RentManagerApp(root, launcher_client=launcher_socket)

        def on_file_path_change(file_path):
            if file_path is None:
                root.title(f'Rent Manager - (new document)')
            else:
                root.title(f'Rent Manager - {Path(file_path).stem}')

        app.file_path_change_listeners.add(on_file_path_change)

        if args.file is not None:
            try:
                app.open_path(args.file)
            except OSError:
                logging.warning(f'Cannot open {args.file}:\n{traceback.format_exc()}')
        app.frame.pack(fill=tk.BOTH, expand=True)

        root.config(menu=app.menu(root))

        def on_close():
            if not app.prompt_unsaved_changes():
                root.destroy()

        root.protocol('WM_DELETE_WINDOW', on_close)

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

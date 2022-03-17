import sys

from PIL import Image


def main():
    if sys.platform.startswith('linux'):
        return
    logo_png = 'logo.png'
    # noinspection SpellCheckingInspection
    icon_type = 'icns' if sys.platform.startswith('darwin') else 'ico'
    # noinspection SpellCheckingInspection
    icon_sizes = [(16 << i, 16 << i) + (1,) * (icon_type == 'icns') for i in range(7)]

    logo_icon = f'logo.{icon_type}'

    Image.open(logo_png).save(logo_icon, format=icon_type, sizes=icon_sizes)


if __name__ == '__main__':
    main()

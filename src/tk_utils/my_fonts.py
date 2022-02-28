import operator
import threading
from tkinter import font
from typing import Optional

registry: dict[tuple, font.Font] = {}


def derived_font(base_name: str, *, family: str = None, size: int = None, weight: str = None) -> font.Font:
    base_font = font.nametofont(base_name).actual()

    def maybe(value, default):
        if value is None:
            return default
        else:
            return value

    new_font_tuple = (
        maybe(family, base_font['family']),
        maybe(size, base_font['size']),
        maybe(weight, base_font['weight'])
    )

    if new_font_tuple in registry:
        return registry[new_font_tuple]
    else:
        new_font = font.Font(
            name=f'derivedFont{id(new_font_tuple)}', exists=False,
            family=new_font_tuple[0],
            size=new_font_tuple[1],
            weight=new_font_tuple[2],
        )
        registry[new_font_tuple] = new_font
        return new_font

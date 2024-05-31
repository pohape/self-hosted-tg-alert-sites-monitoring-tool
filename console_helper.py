from enum import Enum


class Color(Enum):
    TITLE = 1
    ERROR = 91
    WARNING = 93
    SUCCESS = 92
    QUOTATION = 3


def color_text(text, color: Color):
    print(f"\033[{color.value}m{text}\033[0m")

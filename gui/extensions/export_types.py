from typing import TypedDict, Any


class TValue(TypedDict):
    value: Any


class TColor(TypedDict):
    r: int
    g: int
    b: int
    a: int


class TTextColor(TypedDict):
    # Foreground
    r1: int
    g1: int
    b1: int
    a1: int

    # Background
    r2: int
    g2: int
    b2: int
    a2: int

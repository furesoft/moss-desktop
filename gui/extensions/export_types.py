from typing import TypedDict, Any, Optional


class TValue(TypedDict):
    value: Any


class TColor(TypedDict):
    r: int
    g: int
    b: int
    a: Optional[int]


class TTextColor(TypedDict):
    foreground: TColor
    background: Optional[TColor]

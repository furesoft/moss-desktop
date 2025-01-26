from typing import TypedDict, List, Optional


class TContextButton(TypedDict):
    text: str
    icon: str
    context_icon: str
    action: str
    context_menu: str


class TContextMenu(TypedDict):
    key: str
    buttons: List[TContextButton]
    pre_loop: Optional[str]
    post_loop: Optional[str]
    invert: bool

from typing import TypedDict, List

class TButton(TypedDict):
    text: str
    icon: str
    context_icon: str
    action: str
    context_menu: str

class TContextMenu(TypedDict):
    key: str
    buttons: List[TButton]
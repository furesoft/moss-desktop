from abc import ABC
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from gui import GUI
    from melora.injector import Injector


class ExtensionBase(ABC):
    NAME: str = "Unknown"
    SHORT: str = "Unknown"
    ID: str = 'unknown'
    ACTIONS: Dict[str, str] = {}  # Name: Function
    RESOURCES: Dict[str, str] = {}  # Key: Path

    def __init__(self, injector: 'Injector'):
        self.gui: 'GUI' = injector.parent_context
        self.injector: 'Injector' = injector
        self.api = self.gui.api

    def load(self):  # Additional load
        pass

    def event_hook(self, event):  # Provided event hook
        pass

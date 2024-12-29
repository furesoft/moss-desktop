from melora.extension_base import ExtensionBase
from rm_api import SyncRefresh
from rm_api.helpers import threaded


class Extension(ExtensionBase):
    ID = 'root_tools'
    NAME = "Root Tools"
    SHORT = 'RT'
    AUTHOR = "RedTTG"
    ACTIONS = {
        "Reset root": "reset_root",
        "Get current root": "get_root",
    }

    @threaded
    def reset_root(self):
        self.api.reset_root()
        self.api.spread_event(SyncRefresh())

    @threaded
    def get_root(self):
        root = self.api.get_root()
        print(root)

    def save(self):
        pass

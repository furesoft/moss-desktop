from melora.extension_base import ExtensionBase
from rm_api import SyncRefresh


class Extension(ExtensionBase):
    ID = 'root_tools'
    NAME = "Root Tools"
    SHORT = 'RT'
    AUTHOR = "RedTTG"
    ACTIONS = {
        "Reset root": "reset_root"
    }

    def reset_root(self):
        self.api.reset_root()
        self.api.spread_event(SyncRefresh())

    def save(self):
        pass

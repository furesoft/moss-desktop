from functools import lru_cache
from typing import Optional

from gui.pp_helpers import ContextMenu
from .common import INJECTOR_COLOR
from gui import GUI
import pygameextra as pe


class MeloraContextMenu(ContextMenu):
    INVERT = True

    def __init__(self, parent, injector: 'Injector'):
        self.injector = injector
        self.gui = injector.gui
        self.BUTTONS = [{
            "text": "Melora Menu, press M to close",
            "icon": "compass",
            "action": None
        }]
        for extension_id, extension in self.injector.extensions.items():
            for action_name, action_function in extension.ACTIONS.items():
                text = f'{extension.SHORT}: {action_name}'

                self.BUTTONS.append({
                    "text": text,
                    "icon": "cog",
                    "action": f'ACTION={extension_id}/{action_name}'
                })
        super().__init__(parent, (0, self.gui.ratios.main_menu_top_height))

    def __getattr__(self, item):
        if item.startswith("ACTION="):
            extension_id, action_name = item[7:].split("/")

            def action_plus_close():
                getattr(self.injector.extensions[extension_id],
                        self.injector.extensions[extension_id].ACTIONS[action_name])()
                self.close()

            return action_plus_close
        return super().__getattr__(item)


class InjectorMenu(pe.ChildContext):
    LAYER = pe.AFTER_LOOP_LAYER
    parent_context: GUI

    def __init__(self, injector: 'Injector'):
        self.injector = injector
        self.gui = injector.parent_context
        self.open: Optional[MeloraContextMenu] = None
        super().__init__(injector.parent_context)

    def handle_event(self, e):
        if pe.event.key_DOWN(pe.K_m):
            if self.open:
                self.open = None
            else:
                self.open = MeloraContextMenu(self, self.injector)

    @property
    def defaults(self):
        from gui.defaults import Defaults
        return Defaults

    def loop(self):
        if not self.open:
            return
        if self.open.is_closed:
            self.open = None
        else:
            self.open()

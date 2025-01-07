from abc import ABC
from typing import Tuple, TYPE_CHECKING

import pygameextra as pe

from gui.defaults import Defaults
from gui.pp_helpers.context_bar import ContextBar

if TYPE_CHECKING:
    from gui.screens.main_menu import MainMenu


class ContextMenu(ContextBar, ABC):
    ENABLE_OUTLINE = True
    CONTEXT_MENU_OPEN_DIRECTION = 'right'

    def __init__(self, parent: 'MainMenu', topleft: Tuple[int, int]):
        self.left, self.top = topleft
        self.is_closed = False
        self.waiting_for_let_go = True
        self.rect = pe.Rect(0, 0, 0, 0)

        super().__init__(parent)

    def pre_loop(self):
        pe.draw.rect(Defaults.SELECTED if self.INVERT else Defaults.BACKGROUND, self.rect)
        pe.button.action(self.rect, name=f'context_menu<{id(self)}>.blank_space')
        if self.ENABLE_OUTLINE:
            pe.draw.rect(Defaults.LINE_GRAY, self.rect, self.ratios.line)
        super().pre_loop()

    def close(self):
        self.is_closed = True
        self.quick_refresh()

    def post_loop(self):
        if self.waiting_for_let_go:
            if not any(pe.mouse.clicked()):
                self.waiting_for_let_go = False
        elif any(pe.mouse.clicked()) and not self.rect.collidepoint(pe.mouse.pos()):
            self.close()

    def finalize_button_rect(self, buttons, width, height):
        max_width = max(button.area.width for button in buttons)
        x = self.left
        y = self.top
        for button in buttons:
            button.area.topleft = x, y
            button.area.width = max_width
            y += button.area.height
        self.rect = pe.Rect(self.left, self.top, max_width, y - self.top)
        self.rect.clamp_ip(pe.Rect(0, 0, self.width, self.height))
        if self.left != self.rect.left or self.top != self.rect.top:
            self.left, self.top = self.rect.topleft
            self.finalize_button_rect(buttons, width, height)

    def __call__(self, *args, **kwargs):
        self.extension_manager.opened_context_menus.append(getattr(self, 'KEY', self.__class__.__name__))
        super().__call__(*args, **kwargs)

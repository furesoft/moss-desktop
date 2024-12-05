from typing import Tuple

import pygameextra as pe
from abc import ABC

from gui.defaults import Defaults
from gui.pp_helpers.context_bar import ContextBar


class ContextMenu(ContextBar, ABC):

    def __init__(self, parent: 'MainMenu', topleft: Tuple[int, int]):
        self.left, self.top = topleft
        self.can_close = False
        self.waiting_for_let_go = True
        self.rect = pe.Rect(0, 0, 0, 0)
        super().__init__(parent)

    def pre_loop(self):
        pe.draw.rect(Defaults.BACKGROUND, self.rect, 0)
        pe.draw.rect(Defaults.LINE_GRAY, self.rect, self.ratios.line)
        super().pre_loop()

    def close(self):
        self.can_close = True

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

from abc import ABC
from typing import TYPE_CHECKING

import pygameextra as pe

if TYPE_CHECKING:
    from gui import GUI


class ScrollableView(pe.Context, ABC):
    T = 20

    def __init__(self, gui: 'GUI'):
        self.gui = gui
        self.BACKGROUND = self.gui.BACKGROUND
        self._top = 0
        self.active_top = 0
        self.bottom = 0
        super().__init__()

    def handle_event(self, event):
        if not self.gui.ctrl_hold and event.type == pe.MOUSEWHEEL:
            self.active_top += event.y * 50
            # active top is always a negative number

    @property
    def top(self):
        correct_top = min(0, max(self.active_top,
                                 (-self.bottom + self.height) - self.gui.ratios.main_menu_document_padding))
        self.active_top = int(
            (1 - self.T * self.gui.delta_time) * self.active_top + self.T * self.gui.delta_time * correct_top)
        if self.active_top - 5 < self._top < self.active_top + 5:
            return self._top
        self._top = int((1 - self.T * self.gui.delta_time) * self._top + self.T * self.gui.delta_time * self.active_top)

        return self._top

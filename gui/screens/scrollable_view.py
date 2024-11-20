from abc import ABC
from typing import TYPE_CHECKING

import pygameextra as pe

if TYPE_CHECKING:
    from gui import GUI


class ScrollableView(pe.Context, ABC):
    BACKGROUND = pe.colors.red

    def __init__(self, gui: 'GUI'):
        self.gui = gui
        super().__init__()

    # TODO: provide properties to help with scroll

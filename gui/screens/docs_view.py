import pygameextra as pe
from typing import TYPE_CHECKING

from gui.screens.scrollable_view import ScrollableView

if TYPE_CHECKING:
    from gui import GUI


class DocumentTreeViewer(ScrollableView):
    def __init__(self, gui: 'GUI', area: pe.Rect):
        self.gui = gui
        self.AREA = area
    # TODO: Finish this and implement into main menu

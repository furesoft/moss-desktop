from typing import TYPE_CHECKING, Dict

import pygameextra as pe

if TYPE_CHECKING:
    from gui import GUI
    from gui.aspect_ratio import Ratios
    from rm_api import API


class Settings(pe.ChildContext):
    LAYER = pe.AFTER_LOOP_LAYER

    # definitions from GUI
    api: 'API'
    parent_context: 'GUI'
    icons: Dict[str, pe.Image]
    ratios: 'Ratios'

    def __init__(self, parent: 'GUI'):
        super().__init__(parent)

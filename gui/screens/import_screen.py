from typing import Dict, TYPE_CHECKING, List

import pygameextra as pe

from gui.aspect_ratio import Ratios


if TYPE_CHECKING:
    from gui import GUI
    from gui.screens.main_menu import MainMenu
    from rm_api import API, Document


class ImportScreen(pe.ChildContext):
    LAYER = pe.AFTER_LOOP_LAYER

    # definitions from GUI
    api: 'API'
    parent_context: 'GUI'
    icons: Dict[str, pe.Image]
    ratios: 'Ratios'

    documents_to_upload: List['Document']

    def __init__(self, parent: 'GUI'):
        self.documents_to_upload = []
        self.folder = parent.main_menu.navigation_parent
        super().__init__(parent)
        parent.import_screen = self

    def add_item(self, document: 'Document'):
        self.documents_to_upload.append(document)

    def loop(self):
        pass

import threading
from typing import Dict, TYPE_CHECKING, List

import pygameextra as pe
from gui.aspect_ratio import Ratios
from gui.defaults import Defaults
from gui.rendering import render_button_using_text, render_full_text
from rm_api import Document

if TYPE_CHECKING:
    from gui import GUI
    from rm_api import API


class ImportScreen(pe.ChildContext):
    LAYER = pe.AFTER_LOOP_LAYER

    # definitions from GUI
    api: 'API'
    parent_context: 'GUI'
    icons: Dict[str, pe.Image]
    ratios: 'Ratios'
    import_screen: 'ImportScreen'

    documents_to_upload: List['Document']

    def __init__(self, parent: 'GUI'):
        self.documents_to_upload = []
        self.folder = parent.main_menu.navigation_parent
        super().__init__(parent)
        parent.import_screen = self
        self.title = pe.Text("Import", Defaults.MAIN_MENU_FONT, self.ratios.import_screen_title_size,
                             colors=Defaults.TEXT_COLOR)

        self.title.rect.topleft = (
            self.ratios.import_screen_title_padding,
            self.ratios.import_screen_title_padding
        )

        self.texts: Dict[str, pe.Text] = {
            key: pe.Text(
                text,
                Defaults.BUTTON_FONT, self.ratios.import_screen_button_size,
                colors=Defaults.TEXT_COLOR_T)
            for key, text in {
                'cancel': "Cancel",
                'full': "Full Sync",
                'light': "Light Sync",
                'info_text': "Syncs a dummy so that you can archive it, \nbefore syncing the full document ->"
            }.items()
        }

        right = self.width - self.ratios.import_screen_button_margin
        for text in self.texts.values():
            text.rect.height = self.ratios.import_screen_button_size
            text.rect.bottom = self.height - self.ratios.import_screen_button_margin
            text.rect.right = right
            right = text.rect.left - self.ratios.import_screen_button_margin

    def add_item(self, document: 'Document'):
        assert isinstance(document, Document)
        self.documents_to_upload.append(document)

    def loop(self):
        self.title.display()

        render_button_using_text(self.parent_context, self.texts['cancel'], outline=self.ratios.outline,
                                 action=self.close)
        render_button_using_text(self.parent_context, self.texts['full'], outline=self.ratios.outline,
                                 action=self.full_import)
        light_import_rect = render_button_using_text(self.parent_context, self.texts['light'],
                                                     outline=self.ratios.outline,
                                                     action=self.light_import)
        info_icon = self.icons['info']
        info_rect = pe.Rect(0, 0, *info_icon.size)
        info_rect.center = light_import_rect.topright
        pe.button.rect(
            info_rect,
            self.BACKGROUND, self.BACKGROUND,
            hover_draw_action=render_full_text,
            hover_draw_data=(self.parent_context, self.texts['info_text'])
        )
        info_icon.display(info_rect.topleft)

    def close(self):
        self.parent_context.import_screen = None
        del self.screens.queue[-1]

    def full_import(self):
        threading.Thread(
            target=self.api.upload_many_documents,
            args=(self.documents_to_upload,),
            daemon=True
        ).start()
        self.close()

    def light_import(self):
        self.api.upload_many_documents(self.convert_light())

    def convert_light(self):
        light_documents = []

        for document in self.documents_to_upload:
            if document.content.file_type == "pdf":
                light_documents.append(document.replace_pdf(self.data['light_pdf']))

        return light_documents

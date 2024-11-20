from abc import abstractmethod, ABC

import pygameextra as pe
from typing import TYPE_CHECKING, Literal, Dict

from gui.defaults import Defaults
from gui.helpers import shorten_folder_by_size, shorten_folder, shorten_document
from gui.literals import MAIN_MENU_MODES
from gui.rendering import render_document, render_collection
from gui.screens.scrollable_view import ScrollableView

if TYPE_CHECKING:
    from gui import GUI


class DocumentTreeViewer(ScrollableView, ABC):
    def __init__(self, gui: 'GUI', area):
        self.AREA = area
        self.texts: Dict[str, pe.Text] = {}
        super().__init__(gui)

    def handle_texts(self):
        document_collections = dict(self.document_collections)
        documents = dict(self.documents)

        # Preparing the document collection texts
        for uuid, document_collection in document_collections.items():
            if self.texts.get(uuid) is None or self.texts[
                uuid + '_full'
            ].text != document_collection.metadata.visible_name:
                if self.mode == 'list':
                    shortened_text = shorten_folder_by_size(document_collection.metadata.visible_name, self.width)
                else:
                    shortened_text = shorten_folder(document_collection.metadata.visible_name)
                self.texts[uuid] = pe.Text(shortened_text,
                                           Defaults.FOLDER_FONT,
                                           self.gui.ratios.main_menu_label_size, (0, 0), Defaults.TEXT_COLOR)
                self.texts[uuid + '_full'] = pe.Text(document_collection.metadata.visible_name,
                                                     Defaults.FOLDER_FONT,
                                                     self.gui.ratios.main_menu_label_size, (0, 0), Defaults.TEXT_COLOR)

        # Preparing the document texts
        for uuid, document in documents.items():
            if self.texts.get(uuid) is None or self.texts[uuid + '_full'].text != document.metadata.visible_name:
                self.texts[uuid] = pe.Text(shorten_document(document.metadata.visible_name),
                                           Defaults.DOCUMENT_TITLE_FONT,
                                           self.gui.ratios.main_menu_document_title_size, (0, 0),
                                           Defaults.DOCUMENT_TITLE_COLOR)
                self.texts[uuid + '_full'] = pe.Text(document.metadata.visible_name,
                                                     Defaults.DOCUMENT_TITLE_FONT,
                                                     self.gui.ratios.main_menu_document_title_size, (0, 0),
                                                     Defaults.DOCUMENT_TITLE_COLOR)

    @property
    @abstractmethod
    def documents(self):
        return []

    @property
    @abstractmethod
    def document_collections(self):
        return []

    @property
    @abstractmethod
    def mode(self) -> MAIN_MENU_MODES:
        return 'list'

    def loop(self):
        x = 0
        y = 0

        # Rendering the folders
        document_collection_width = \
            self.gui.ratios.main_menu_document_width if self.mode == 'grid' else self.width - x * 2
        for i, document_collection in enumerate(self.gui.main_menu.get_sorted_document_collections()):
            render_collection(self.gui, document_collection, self.texts,
                              self.gui.main_menu.set_parent, x, y, document_collection_width)

            if self.mode == 'grid':
                x += self.gui.ratios.main_menu_document_width + self.gui.ratios.main_menu_document_padding
                if x + self.gui.ratios.main_menu_document_width > self.width and i + 1 < len(self.document_collections):
                    x = self.gui.ratios.main_menu_x_padding
                    y += self.gui.ratios.main_menu_folder_height_distance
            else:
                y += self.gui.ratios.main_menu_folder_height_distance

        # Resetting the x and y for the documents
        if len(self.document_collections) > 0:
            y += self.gui.ratios.main_menu_folder_height_last_distance
        else:
            y = self.gui.ratios.main_menu_my_files_only_documents_padding

        x = 0

        # Rendering the documents
        for i, document in enumerate(self.gui.main_menu.get_sorted_documents()):
            rect = pe.Rect(
                x, y,
                self.gui.ratios.main_menu_document_width,
                self.gui.ratios.main_menu_document_height
            )
            if document.uuid in self.gui.main_menu.document_sync_operations:
                document_sync_operation = self.gui.main_menu.document_sync_operations[document.uuid]
                if document_sync_operation.finished:
                    del self.gui.main_menu.document_sync_operations[document.uuid]
                    document_sync_operation = None
            else:
                document_sync_operation = None
            render_document(self.gui, rect, self.texts, document, document_sync_operation)

            x += self.gui.ratios.main_menu_document_width + self.gui.ratios.main_menu_document_padding
            if x + self.gui.ratios.main_menu_document_width > self.width and i + 1 < len(self.documents):
                x = self.gui.ratios.main_menu_x_padding
                y += self.gui.ratios.main_menu_document_height + self.gui.ratios.main_menu_document_height_distance

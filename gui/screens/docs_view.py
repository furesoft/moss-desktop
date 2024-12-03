from abc import abstractmethod, ABC
from math import ceil

import pygameextra as pe
from typing import TYPE_CHECKING, Literal, Dict

from gui.defaults import Defaults
from gui.helpers import dynamic_text
from gui.literals import MAIN_MENU_MODES
from gui.rendering import render_document, render_collection
from gui.screens.scrollable_view import ScrollableView

if TYPE_CHECKING:
    from gui import GUI


class DocumentTreeViewer(ScrollableView, ABC):
    def __init__(self, gui: 'GUI', area):
        self.AREA = area
        self.texts: Dict[str, pe.Text] = {}
        self.x_padding_collections = 0
        self.x_padding_documents = 0
        self.last_width = None
        self._scale = self.gui.config.doc_view_scale
        super().__init__(gui)

    def handle_texts(self):
        document_collections = dict(self.document_collections)
        documents = dict(self.documents)

        # Preparing the document collection texts
        font_details = (Defaults.FOLDER_TITLE_FONT, self.gui.ratios.document_tree_view_folder_title_size)
        for uuid, document_collection in document_collections.items():
            if self.texts.get(uuid) is None or self.texts[
                uuid + '_full'
            ].text != document_collection.metadata.visible_name:
                shortened_text = dynamic_text(document_collection.metadata.visible_name, *font_details, self.document_width if self.mode == 'grid' else self.width)
                self.texts[uuid] = pe.Text(shortened_text, *font_details, (0, 0), Defaults.TEXT_COLOR)
                self.texts[uuid + '_full'] = pe.Text(document_collection.metadata.visible_name,
                                                     *font_details, (0, 0), Defaults.TEXT_COLOR)

        # Preparing the document texts
        font_details = (Defaults.DOCUMENT_TITLE_FONT, self.gui.ratios.document_tree_view_document_title_size)
        for uuid, document in documents.items():
            if self.texts.get(uuid) is None or self.texts[uuid + '_full'].text != document.metadata.visible_name:
                shortened_text = dynamic_text(document.metadata.visible_name, *font_details, self.document_width if self.mode == 'grid' else self.width)
                self.texts[uuid] = pe.Text(shortened_text, *font_details
                                           , (0, 0),
                                           Defaults.DOCUMENT_TITLE_COLOR)
                self.texts[uuid + '_full'] = pe.Text(document.metadata.visible_name, *font_details, (0, 0),
                                                     Defaults.DOCUMENT_TITLE_COLOR)

    @property
    @abstractmethod
    def documents(self):
        return {}

    @property
    @abstractmethod
    def document_collections(self):
        return {}

    @property
    @abstractmethod
    def mode(self) -> MAIN_MENU_MODES:
        return 'list'

    def pre_loop(self):
        area_of_widths = self.width / (
                self.document_width + self.gui.ratios.main_menu_document_padding
        ) - self.gui.ratios.main_menu_document_padding / self.width
        area_of_widths = max(1, int(area_of_widths))

        width = area_of_widths * self.document_width
        width += self.gui.ratios.main_menu_document_padding * (area_of_widths - 1)

        padding = (self.width - width) / 2

        collections_rows = 1
        documents_rows = 1

        if len(self.document_collections) == 0:
            collections_rows = 0
        if len(self.document_collections) < area_of_widths:
            self.x_padding_collections = self.gui.ratios.main_menu_x_padding
        else:
            self.x_padding_collections = padding
            if self.mode == 'grid':
                collections_rows = ceil(len(self.document_collections) / area_of_widths)
            else:
                collections_rows = len(self.document_collections)

        if len(self.documents) == 0:
            documents_rows = 0
        if len(self.documents) < area_of_widths:
            self.x_padding_documents = self.gui.ratios.main_menu_x_padding
        else:
            self.x_padding_documents = padding
            documents_rows = ceil(len(self.documents) / area_of_widths)

        if len(self.document_collections) > 0:
            # Collections
            y = self.gui.ratios.main_menu_top_padding / 2
            y += self.gui.ratios.main_menu_folder_height_distance * collections_rows
        else:
            y = 0

        # Documents
        y += (self.document_height + self.gui.ratios.main_menu_document_height_distance) * documents_rows

        if len(self.documents) > 0:
            y -= self.gui.ratios.main_menu_document_title_height_margin * 2

        self.bottom = y + self.gui.ratios.bottom_bar_height

        super().pre_loop()

    def loop(self):
        top = self.top
        if self.mode == 'grid':
            collections_x = self.x_padding_collections
        else:
            collections_x = self.gui.ratios.main_menu_x_padding

        x = collections_x

        y = self.gui.ratios.main_menu_top_padding / 2
        y += top

        # Rendering the folders
        document_collection_width = \
            self.document_width if self.mode == 'grid' else self.width - self.gui.ratios.main_menu_x_padding * 2
        for i, document_collection in enumerate(
                self.gui.main_menu.get_sorted_document_collections(self.document_collections.values())):
            render_collection(self.gui, document_collection, self.texts,
                              self.gui.main_menu.set_parent, x, y, document_collection_width)

            if self.mode == 'grid':
                x += self.document_width + self.gui.ratios.main_menu_document_padding
                if x + self.document_width > self.width and i + 1 < len(self.document_collections):
                    x = collections_x
                    y += self.gui.ratios.main_menu_folder_height_distance
            else:
                y += self.gui.ratios.main_menu_folder_height_distance

        # Resetting the x and y for the documents
        if len(self.document_collections) > 0:
            y += self.gui.ratios.main_menu_folder_height_last_distance
        else:
            y = top

        x = self.x_padding_documents

        # Rendering the documents
        full_document_heigth = self.document_height + self.gui.ratios.main_menu_document_height_distance
        for i, document in enumerate(self.gui.main_menu.get_sorted_documents(self.documents.values())):
            if y + full_document_heigth > 0:
                # Render the document
                rect = pe.Rect(
                    x, y,
                    self.document_width,
                    self.document_height
                )
                if document.uuid in self.gui.main_menu.document_sync_operations:
                    document_sync_operation = self.gui.main_menu.document_sync_operations[document.uuid]
                    if document_sync_operation.finished:
                        del self.gui.main_menu.document_sync_operations[document.uuid]
                        document_sync_operation = None
                else:
                    document_sync_operation = None
                render_document(self.gui, rect, self.texts, document, document_sync_operation,
                                self.scale)

            x += self.document_width + self.gui.ratios.main_menu_document_padding
            if x + self.document_width > self.width and i + 1 < len(self.documents):
                x = self.x_padding_documents
                y += full_document_heigth
            if y > self.height:
                break

    @property
    def document_width(self):
        return self.gui.ratios.main_menu_document_width * self.scale

    @property
    def document_height(self):
        return self.gui.ratios.main_menu_document_height * self.scale

    def handle_event(self, event):
        super().handle_event(event)
        if not self.gui.ctrl_hold:
            return

        # Handle scrolling to change the scale
        if event.type == pe.pygame.MOUSEWHEEL:
            if event.y > 0:
                self.scale += 0.1
            else:
                self.scale -= 0.1
            self.scale = max(0.5, min(2.08, self.scale))
            self.texts.clear()
            self.handle_texts()

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, value):
        self._scale = value
        self.gui.config.doc_view_scale = value
        self.gui.dirty_config = True

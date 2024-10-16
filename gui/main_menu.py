import time
from queue import Queue
from typing import TYPE_CHECKING, Dict

import pygameextra as pe

from .defaults import Defaults
from .helpers import shorten_name, shorten_path, shorten_folder, shorten_document
from .rendering import render_document, render_collection, render_header, draw_bottom_loading_bar

if TYPE_CHECKING:
    from gui import GUI
    from rm_api import API
    from .loader import Loader


class MainMenu(pe.ChildContext):
    LAYER = pe.AFTER_LOOP_LAYER

    api: 'API'
    parent_context: 'GUI'
    icons: Dict[str, pe.Image]
    SORTING_FUNCTIONS = {
        'last_modified': lambda item: item.metadata.last_modified,
    }

    def __init__(self, parent: 'GUI'):
        self.navigation_parent = None
        self.document_collections = {}
        self.documents = {}
        self.texts: Dict[str, pe.Text] = {}
        self.path_queue = Queue()
        # TODO: Maybe load from settings
        self.current_sorting_mode = 'last_modified'
        # reversed is equivalent to descending
        # obviously, non reversed is ascending
        self.current_sorting_reverse = True
        super().__init__(parent)
        if 'screenshot' in self.icons:
            self.icons['screenshot'].set_alpha(100)
        self.get_items()

        self.texts['my_files'] = pe.Text("My files", Defaults.MAIN_MENU_FONT, self.ratios.main_menu_my_files_size,
                                         (0, 0), Defaults.TEXT_COLOR)
        self.texts['my_files'].rect.topleft = (
            self.ratios.main_menu_x_padding, self.ratios.main_menu_top_height + self.ratios.main_menu_top_padding)

    def get_items(self):
        # Copy the document collections and documents incase they change
        document_collections = dict(self.api.document_collections)
        documents = dict(self.api.documents)

        # Filtering the document collections and documents with the current parent
        self.document_collections = {
            key: item for key, item in
            document_collections.items()
            if item.parent == self.navigation_parent
        }
        self.documents = {
            key: item for key, item in
            documents.items()
            if item.parent == self.navigation_parent
        }

        # Preparing the document collection texts
        for uuid, document_collection in document_collections.items():
            if self.texts.get(uuid) is None:
                self.texts[uuid] = pe.Text(shorten_folder(document_collection.metadata.visible_name),
                                           Defaults.FOLDER_FONT,
                                           self.ratios.main_menu_label_size, (0, 0), Defaults.TEXT_COLOR)

        # Preparing the document texts
        for uuid, document in documents.items():
            if self.texts.get(uuid) is None:
                self.texts[uuid] = pe.Text(shorten_document(document.metadata.visible_name),
                                           Defaults.DOCUMENT_TITLE_FONT,
                                           self.ratios.main_menu_document_title_size, (0, 0), Defaults.DOCUMENT_TITLE_COLOR)
                self.texts[uuid+'_full'] = pe.Text(document.metadata.visible_name,
                                           Defaults.DOCUMENT_TITLE_FONT,
                                           self.ratios.main_menu_document_title_size, (0, 0), Defaults.DOCUMENT_TITLE_COLOR)

        # Preparing the path queue and the path texts
        self.path_queue.queue.clear()
        if self.navigation_parent is not None:
            parent = self.navigation_parent
            while parent is not None:
                self.path_queue.put(parent)
                text_key = f'path_{parent}'

                # Render the path text
                if self.texts.get(text_key) is None:
                    self.texts[text_key] = pe.Text(
                        shorten_path(document_collections[parent].metadata.visible_name),
                        Defaults.PATH_FONT,
                        self.ratios.main_menu_path_size,
                        (0, 0), Defaults.TEXT_COLOR
                    )

                parent = document_collections[parent].parent

    def pre_loop(self):
        pe.fill.interlace((240, 240, 240), 5)
        if 'screenshot' in self.icons:
            self.icons['screenshot'].display()

    def set_parent(self, uuid=None):
        self.navigation_parent = uuid
        self.get_items()
        self.quick_refresh()

    def get_sorted_document_collections(self):
        return sorted(self.document_collections.values(), key=lambda item: item.metadata.visible_name)

    def get_sorted_documents(self):
        documents = sorted(self.documents.values(), key=self.SORTING_FUNCTIONS[self.current_sorting_mode])
        if self.current_sorting_reverse:
            return reversed(documents)
        return documents

    def loop(self):
        pe.draw.line(Defaults.LINE_GRAY, (0, self.ratios.main_menu_top_height),
                     (self.width, self.ratios.main_menu_top_height), self.ratios.pixel(2))

        render_header(self.parent_context, self.texts, self.set_parent, self.path_queue)

        x = self.ratios.main_menu_x_padding
        y = self.texts['my_files'].rect.bottom + self.ratios.main_menu_my_files_folder_padding

        # Rendering the folders
        for i, document_collection in enumerate(self.get_sorted_document_collections()):

            render_collection(self.parent_context, document_collection, self.texts[document_collection.uuid],
                              self.set_parent, x, y)

            x += self.ratios.main_menu_folder_distance
            if i % 4 == 3 and i != len(self.document_collections) - 1:
                x = self.ratios.main_menu_x_padding
                y += self.ratios.main_menu_folder_height_distance

        # Resetting the x and y for the documents
        if len(self.document_collections) > 0:
            y += self.ratios.main_menu_folder_height_last_distance
        else:
            y = self.texts['my_files'].rect.bottom + self.ratios.main_menu_my_files_only_documents_padding

        x = self.ratios.main_menu_x_padding

        # Rendering the documents
        for i, document in enumerate(self.get_sorted_documents()):
            rect = pe.Rect(
                x, y,
                self.ratios.main_menu_document_width,
                self.ratios.main_menu_document_height
            )

            render_document(self.parent_context, rect, self.texts, document)

            x += self.ratios.main_menu_document_width + self.ratios.main_menu_document_padding
            if i % 4 == 3:
                x = self.ratios.main_menu_x_padding
                y += self.ratios.main_menu_document_height + self.ratios.main_menu_document_height_distance

    def post_loop(self):
        loader: 'Loader' = self.parent_context.screens.queue[0]
        if loader.files_to_load is not None:
            draw_bottom_loading_bar(self.parent_context)
            # Update the data if the loader has loaded more files
            if loader.loading_feedback + 3 < loader.files_loaded:
                self.get_items()
                loader.loading_feedback = loader.files_loaded
        elif loader.loading_feedback:
            self.get_items()
            loader.loading_feedback = 0

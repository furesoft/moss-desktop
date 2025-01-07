from typing import TYPE_CHECKING

import pygameextra as pe

from gui.cloud_action_helper import import_notebook_pages_to_cloud
from gui.defaults import Defaults
from gui.file_prompts import notebook_prompt
from gui.pp_helpers import ContextMenu
from gui.preview_handler import PreviewHandler
from gui.screens.guides import Guides
from gui.screens.name_field_screen import NameFieldScreen
from gui.screens.viewer import DocumentViewer
from rm_api.models import Document, DocumentCollection
from rm_api.notifications.models import DocumentSyncProgress

if TYPE_CHECKING:
    pass


class ImportContextMenu(ContextMenu):
    BUTTONS = (
        {
            "text": "PDF/EPUB Import",
            "icon": "import",
            "action": 'import_action'
        },
        {
            "text": "Notebook Import",
            "icon": "notebook_add",
            "action": 'notebook_import'
        }
    )

    def import_action(self):
        self.main_menu.bar.import_action()
        self.close()

    def _notebook_import(self, title: str):
        notebook_prompt(lambda file_paths: import_notebook_pages_to_cloud(self.main_menu, file_paths, title))

    def notebook_import(self):
        NameFieldScreen(self.main_menu.parent_context, "Import Notebook", "", self._notebook_import, None, )
        self.close()


class DeleteContextMenu(ContextMenu):
    BUTTONS = (
        {
            "text": "Delete",
            "icon": "trashcan_delete",
            "action": 'delete_confirm'
        },
    )
    INVERT = True

    def delete_confirm(self):
        self.main_menu.bar.delete_confirm()
        self.close()


class DebugContextMenu(ContextMenu):
    DEBUG_FOLDER = 'debug'
    DEBUG_PREVIEW = 'debug_preview'
    DEBUG_PREVIEW_PAGE_INDEX = 'debug'
    PREVIEW_COLORS = (
        (255, 255, 255),
        (200, 200, 200),
        (150, 150, 150),
        (100, 100, 100),
        (50, 50, 50),
        (20, 20, 20),
        (0, 0, 0),
        (255, 0, 0),
        (200, 0, 0),
        (150, 0, 0),
        (100, 0, 0),
        (50, 0, 0),
        (20, 0, 0),
        (0, 255, 0),
        (0, 200, 0),
        (0, 150, 0),
        (0, 100, 0),
        (0, 50, 0),
        (0, 20, 0),
        (0, 0, 255),
        (0, 0, 200),
        (0, 0, 150),
        (0, 0, 100),
        (0, 0, 50),
        (0, 0, 20),
        (255, 255, 0),
        (200, 200, 0),
        (150, 150, 0),
        (100, 100, 0),
        (50, 50, 0),
        (20, 20, 0),
        (0, 255, 255),
        (0, 200, 200),
        (0, 150, 150),
        (0, 100, 100),
        (0, 50, 50),
        (0, 20, 20),
        (255, 0, 255),
        (200, 0, 200),
        (150, 0, 150),
        (100, 0, 100),
        (50, 0, 50),
        (20, 0, 20),

    )
    BUTTONS = (
        {
            "text": "Global debug menu",
            "icon": "cog",
            "action": None
        },
        {
            "text": "Test doc view",
            "icon": "notebook",
            "action": "test_doc_view"
        },
        {
            "text": "Hot reload",
            "icon": "rotate",
            "action": "hot_reload"
        }
    )

    def hot_reload(self):
        self.reload()

    def test_doc_view(self):
        if not PreviewHandler.CACHED_PREVIEW.get(self.DEBUG_PREVIEW):
            surface = pe.Surface((len(self.PREVIEW_COLORS) * 10, 100))
            with surface:
                for i, color in enumerate(self.PREVIEW_COLORS):
                    pe.draw.rect(color, (i * 10, 0, 10, surface.height))
            PreviewHandler.CACHED_PREVIEW[self.DEBUG_PREVIEW] = (self.DEBUG_PREVIEW_PAGE_INDEX, pe.Image(surface))

        for document in list(self.api.documents.values()):
            if document.parent == self.DEBUG_FOLDER:
                self.api.documents.pop(document.uuid)
        for document_collection in list(self.api.document_collections.values()):
            if document_collection.parent == self.DEBUG_FOLDER:
                self.api.document_collections.pop(document_collection.uuid)

        self.apply(DocumentCollection.create(self.api, "Folder", self.DEBUG_FOLDER))
        self.apply(folder_with_tag := DocumentCollection.create(self.api, "Folder /w tag", self.DEBUG_FOLDER))
        self.apply(folder_with_star := DocumentCollection.create(self.api, "Folder /w star", self.DEBUG_FOLDER))
        self.apply(Document.new_notebook(self.api, "Normal notebook", self.DEBUG_FOLDER))
        self.apply(notebook_with_tag := Document.new_notebook(self.api, "Notebook /w tag", self.DEBUG_FOLDER))
        self.apply(notebook_with_star := Document.new_notebook(self.api, "Notebook /w star", self.DEBUG_FOLDER))
        self.apply(problematic_notebook := Document.new_notebook(self.api, "Problematic notebook", self.DEBUG_FOLDER))
        self.apply(syncing_notebook := Document.new_notebook(self.api, "Syncing notebook", self.DEBUG_FOLDER))

        # Document collections
        folder_with_tag.tags.append('Test tag')

        folder_with_star.metadata.pinned = True

        # Notebooks
        DocumentViewer.PROBLEMATIC_DOCUMENTS.add(problematic_notebook.uuid)

        notebook_with_tag.content.tags.append('Test tag')
        notebook_with_star.metadata.pinned = True

        progress = DocumentSyncProgress(syncing_notebook.uuid)
        progress.total = 2
        progress.done = 1
        self.api.spread_event(progress)

        # Set the navigation parent
        self.main_menu.navigation_parent = self.DEBUG_FOLDER

    def apply(self, item):
        if isinstance(item, DocumentCollection):
            self.api.document_collections[item.uuid] = item
        elif isinstance(item, Document):
            self.api.documents[item.uuid] = item
            item.provision = True
            item.content.c_pages.pages[0].id = self.DEBUG_PREVIEW_PAGE_INDEX
            PreviewHandler.CACHED_PREVIEW[item.uuid] = PreviewHandler.CACHED_PREVIEW[self.DEBUG_PREVIEW]


class SideBar(ContextMenu):
    ENABLE_OUTLINE = False
    BUTTONS = (
        {
            "text": "My Files",
            "icon": "my_files",
            "action": "set_location",
            "data": "my_files",
            "inverted_id": "my_files"
        },
        {
            "text": "Filter by",
            "icon": "filter",
            "action": None,
            "inverted_id": "filter",
            "disabled": True,
            "context_icon": "chevron_right",
        },
        {
            "text": "Favorites",
            "icon": "star",
            "action": None,
            "inverted_id": "favorites",
            "disabled": True
        },
        {
            "text": "Tags",
            "icon": "tag",
            "action": None,
            "inverted_id": "tags",
            "disabled": True
        },
        {
            "text": "Trash",
            "icon": "trashcan",
            "action": "set_location",
            "data": "trash",
            "inverted_id": "trash"
        },
        {
            "text": "Made by RedTTG",
            "icon": "heart",
            "action": None
        },
        {
            "text": "Guides",
            "icon": "compass",
            "action": "guides"
        },
        {
            "text": "Settings",
            "icon": "cog",
            "action": "settings",
            "disabled": True
        }
    )

    def __init__(self, context, *args, **kwargs):
        if context.config.debug:
            self.BUTTONS = (*self.BUTTONS, {
                "text": "DEBUG",
                "icon": "cog",
                "action": "debug",
                "context_icon": "chevron_right",
            })
        super().__init__(context, *args, **kwargs)
        self.CONTEXT_MENU_OPEN_PADDING = self.ratios.seperator - self.ratios.line

    def pre_loop(self):
        super().pre_loop()
        pe.draw.line(Defaults.LINE_GRAY, self.rect.topright, self.rect.bottomright, self.ratios.seperator)

    def set_location(self, menu_location: str):
        self.main_menu.menu_location = menu_location
        self.close()

    def settings(self):
        self.close()

    def guides(self):
        self.screens.put(Guides(self.parent_context))
        self.close()

    def debug(self):
        self.handle_new_context_menu(self.debug_context_menu, len(self.BUTTONS) - 1)

    def debug_context_menu(self, ideal_position):
        return DebugContextMenu(self.main_menu, ideal_position)

    def finalize_button_rect(self, buttons, width, height):
        # Rescale the buttons
        for button in buttons:
            button.area.width = self.ratios.main_menu_side_bar_width
            button.area.height = self.ratios.main_menu_top_height
            button.area.left = self.left

        # Position the top 4 buttons
        y = self.top
        for button in buttons[:4]:
            button.area.top = y
            y += button.area.height

        # Position the bottom buttons
        y = self.height
        for button in reversed(buttons[4:]):
            button.area.bottom = y
            y -= button.area.height
        self.rect = pe.Rect(self.left, self.top, self.ratios.main_menu_side_bar_width, self.height)

    @property
    def button_margin(self):
        return self.main_menu.bar.buttons[0].area.left + self.main_menu.bar.button_padding

    @property
    def currently_inverted(self):
        return self.main_menu.menu_location

import time
from abc import abstractmethod, ABC
from functools import lru_cache, wraps
from queue import Queue
from threading import Lock, Thread
from typing import TYPE_CHECKING, Dict, List, Tuple, Union

import pygameextra as pe

from gui.cloud_action_helper import import_files_to_cloud, import_notebook_pages_to_cloud
from gui.events import ResizeEvent
from gui.file_prompts import import_prompt, notebook_prompt
from gui.pp_helpers import ContextMenu, ContextBar
from gui.rendering import draw_bottom_loading_bar, get_bottom_bar_rect, render_header
from gui.screens.docs_view import DocumentTreeViewer
from gui.screens.name_field_screen import NameFieldScreen
from rm_api.notifications.models import SyncRefresh, FileSyncProgress, NewDocuments, DocumentSyncProgress
from rm_api.models import Document, DocumentCollection

from gui.defaults import Defaults
from gui.helpers import shorten_path

if TYPE_CHECKING:
    from gui import GUI
    from gui.aspect_ratio import Ratios
    from rm_api import API
    from gui.screens.loader import Loader


def threaded(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        Thread(target=func, args=args, kwargs=kwargs).start()

    return wrapper


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


class TopBar(ContextBar):
    BUTTONS = (
        {
            "text": "Menu",
            "icon": "burger",
            "action": 'open_menu'
        },
        {
            "text": "Notebook",
            "icon": "notebook_add",
            "action": 'create_notebook'
        }, {
            "text": "Folder",
            "icon": "folder_add",
            "action": 'create_collection'
        }, {
            "text": "Import",
            "icon": "import",
            "action": 'import_action',
            "context_menu": 'import_context',
            "context_icon": "small_chevron_down"
        }, {
            "text": "Export",
            "icon": "export",
            "action": None,
            "disabled": True
        }
    )

    def __init__(self, parent):
        if parent.api.offline_mode:
            for button in self.BUTTONS:
                if button['action'] in ['create_notebook', 'create_collection', 'import_action']:
                    button['disabled'] = True
        super().__init__(parent)
        if self.api.offline_mode:
            self.offline_error_text = pe.Text(
                "You are offline!",
                Defaults.MAIN_MENU_BAR_FONT, parent.ratios.main_menu_bar_size,
                colors=Defaults.TEXT_ERROR_COLOR
            )
            self.update_offline_error_text()

    def update_offline_error_text(self):
        self.offline_error_text.rect.bottomright = (self.width - self.ratios.main_menu_button_margin, self.ratios.main_menu_top_height)

    def handle_scales(self):
        super().handle_scales()
        if self.api.offline_mode:
            self.update_offline_error_text()

    def post_loop(self):
        super().post_loop()
        if self.api.offline_mode:
            self.offline_error_text.display()

    def finalize_button_rect(self, buttons, width, height):
        width += (len(self.BUTTONS) - 2) * self.ratios.main_menu_bar_padding
        width -= buttons[0].area.width
        x = self.width / 2
        x -= width / 2
        margin = (self.ratios.main_menu_top_height - buttons[0].area.height) / 2
        buttons[0].area.left = margin
        buttons[0].area.top = margin
        for button in buttons[1:]:
            button.area.left = x
            x = button.area.right + self.ratios.main_menu_bar_padding

    def create_notebook(self):
        NameFieldScreen(self.parent_context, "New Notebook", "", self._create_notebook, None,
                        submit_text='Create notebook')

    def create_collection(self):
        NameFieldScreen(self.parent_context, "New Folder", "", self._create_collection, None,
                        submit_text='Create folder')

    @threaded
    def _create_notebook(self, title):
        doc = Document.new_notebook(self.api, title, self.main_menu.navigation_parent)
        self.api.upload(doc)

    @threaded
    def _create_collection(self, title):
        col = DocumentCollection.create(self.api, title, self.main_menu.navigation_parent)
        self.api.upload(col)

    def import_action(self):
        import_prompt(lambda file_paths: import_files_to_cloud(self.parent_context, file_paths))

    def import_context(self, ideal_position):
        return ImportContextMenu(self.main_menu, ideal_position)

    def open_menu(self):
        self.main_menu.hamburger()


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
            "icon": "trashcan",
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
            "text": "Settings",
            "icon": "cog",
            "action": "settings",
            "disabled": True
        }
    )

    def pre_loop(self):
        super().pre_loop()
        pe.draw.line(Defaults.LINE_GRAY, self.rect.topright, self.rect.bottomright, self.ratios.seperator)

    def set_location(self, menu_location: str):
        self.main_menu.menu_location = menu_location
        self.close()

    def settings(self):
        self.close()

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


class MainMenuDocView(DocumentTreeViewer):
    main_menu: 'MainMenu'

    def __init__(self, gui: 'GUI'):
        self.gui = gui
        pos, size = self.area_within_main_menu
        super().__init__(gui, (*pos, *size))

    def update_size(self):
        pos, size = self.area_within_main_menu
        self.position = pos
        self.resize(size)

    @property
    def area_within_main_menu(self):
        return (pos := (
            0,
            self.gui.main_menu.texts['my_files'].rect.bottom + self.gui.ratios.main_menu_top_padding,
        )), (
            self.gui.width,
            self.gui.height - pos[1]
        )

    @property
    def documents(self):
        return self.gui.main_menu.documents

    @property
    def document_collections(self):
        return self.gui.main_menu.document_collections

    @property
    def mode(self):
        return self.gui.config.main_menu_view_mode


class MainMenu(pe.ChildContext):
    LAYER = pe.AFTER_LOOP_LAYER

    # definitions from GUI
    api: 'API'
    parent_context: 'GUI'
    icons: Dict[str, pe.Image]
    ratios: 'Ratios'

    SORTING_FUNCTIONS = {
        'last_modified': lambda item: item.metadata.last_modified,
    }

    HEADER_TEXTS = {
        'my_files': "My files",
        'trash': "Trash",
        'favorites': "Favorites",
        'tags': "Tags",
        'notebooks': "Notebooks",
        'pdfs': "PDFs",
        'ebooks': "Ebooks",
    }

    SMALL_HEADER_TEXTS = {
    }

    MAINTAIN_TEXT_KEYS = (
        *HEADER_TEXTS.keys(),
        *SMALL_HEADER_TEXTS.keys(),
        'debug'
    )

    LOCATION_PARENT_MAPPING = {
        'my_files': None,
        'trash': 'trash',
    }

    file_sync_operation: Union[None, FileSyncProgress]

    resync_icon: pe.Image
    resync_rect: pe.Rect
    hamburger_icon: pe.Image
    hamburger_rect: pe.Rect
    doc_view: MainMenuDocView

    def __init__(self, parent: 'GUI'):
        self._navigation_parent = parent.config.last_opened_folder
        self.document_collections = {}
        self.documents = {}
        self.texts: Dict[str, pe.Text] = {}
        self.path_queue = Queue()
        self.call_lock = Lock()
        self.file_sync_operation = None
        parent.api.add_hook("main_menu_cache_invalidator", self.api_event_hook)
        # TODO: Maybe load from settings
        self.current_sorting_mode = 'last_modified'
        # reversed is equivalent to descending
        # obviously, non reversed is ascending
        self.current_sorting_reverse = True
        super().__init__(parent)
        parent.main_menu = self  # Assign myself as the main menu
        self.bar = TopBar(self)
        if 'screenshot' in self.icons:
            self.icons['screenshot'].set_alpha(100)

        # Header texts
        for key, text in self.HEADER_TEXTS.items():
            self.texts[key] = pe.Text(text, Defaults.MAIN_MENU_FONT, self.ratios.main_menu_my_files_size,
                                      (0, 0), Defaults.TEXT_COLOR)
            self.texts[key].rect.topleft = (
                self.ratios.main_menu_x_padding, self.ratios.main_menu_top_height + self.ratios.main_menu_top_padding)
        for key, text in self.SMALL_HEADER_TEXTS.items():
            self.texts[key] = pe.Text(text, Defaults.MAIN_MENU_BAR_FONT, self.ratios.main_menu_bar_size,
                                      (0, 0), Defaults.TEXT_COLOR)

        # Document debug button text
        self.texts['debug'] = pe.Text(
            'DEBUG',
            Defaults.DEBUG_FONT,
            self.ratios.small_debug_text_size,
            colors=Defaults.TEXT_COLOR_H
        )

        self.doc_view = MainMenuDocView(parent)
        self.side_bar = SideBar(self, (0, 0))
        self.side_bar.is_closed = True
        self.get_items()

        self.document_sync_operations: Dict[str, DocumentSyncProgress] = {}
        self.rect_calculations()

    @property
    def navigation_parent(self):
        return self._navigation_parent

    @navigation_parent.setter
    def navigation_parent(self, uuid):
        self._navigation_parent = uuid
        if all((
                self.menu_location == 'my_files',
                self.config.save_last_opened_folder,
                self.config.last_opened_folder != uuid
        )):
            self.config.last_opened_folder = uuid
            self.parent_context.dirty_config = True
        self.get_items()
        self.quick_refresh()

    @property
    def view_mode(self):
        return self.config.main_menu_view_mode

    @view_mode.setter
    def view_mode(self, value):
        self.config.main_menu_view_mode = value
        self.parent_context.dirty_config = True

    @property
    def menu_location(self):
        return self.config.main_menu_menu_location

    @menu_location.setter
    def menu_location(self, value):
        self.config.main_menu_menu_location = value
        self.parent_context.dirty_config = True
        if value == 'trash':
            self.navigation_parent = 'trash'
        elif value == 'my_files':
            self.navigation_parent = self.config.last_opened_folder

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        self.bar()

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

        # Preparing the path queue and the path texts
        self.path_queue.queue.clear()
        if self.navigation_parent is not None:
            parent = self.navigation_parent
            while parent is not None:
                self.path_queue.put(parent)
                text_key = f'path_{parent}'

                # Render the path text
                if self.texts.get(text_key) is None:
                    try:
                        text = shorten_path(document_collections[parent].metadata.visible_name)
                    except:
                        del self.path_queue.queue[-1]
                        parent = None
                        continue
                    self.texts[text_key] = pe.Text(
                        text,
                        Defaults.PATH_FONT,
                        self.ratios.main_menu_path_size,
                        (0, 0), Defaults.TEXT_COLOR
                    )
                try:
                    parent = document_collections[parent].parent
                except KeyError:
                    parent = None
        self.doc_view.handle_texts()

    def pre_loop(self):
        if 'screenshot' in self.icons:
            self.icons['screenshot'].display()
        if not self.side_bar.is_closed:
            self.side_bar()

    def set_parent(self, uuid=None):  # This function is from before navigation_parent was a property
        self.navigation_parent = uuid or self.LOCATION_PARENT_MAPPING[self.menu_location]

    @staticmethod
    def get_sorted_document_collections(old_document_collections) -> sorted:
        return sorted(old_document_collections, key=lambda item: item.metadata.visible_name)

    def get_sorted_documents(self, original_documents_list: List['Document']) -> Union[List['Document'], reversed]:
        documents = sorted(original_documents_list, key=self.SORTING_FUNCTIONS[self.current_sorting_mode])
        if self.current_sorting_reverse:
            return reversed(documents)
        return documents

    def refresh(self):
        if self.api.sync_notifiers < 1:
            self.api.spread_event(SyncRefresh())

    def hamburger(self):
        self.side_bar.is_closed = False

    def loop(self):
        pe.draw.line(Defaults.LINE_GRAY, (0, self.ratios.main_menu_top_height),
                     (self.width, self.ratios.main_menu_top_height), self.ratios.line)

        render_header(self.parent_context, self.texts, self.set_parent, self.path_queue)

        self.resync_icon.display(self.resync_rect.topleft)
        pe.button.rect(
            self.ratios.pad_button_rect(self.resync_rect),
            Defaults.TRANSPARENT_COLOR, Defaults.BUTTON_ACTIVE_COLOR,
            action=self.refresh, name='main_menu.refresh',
            disabled=Defaults.BUTTON_DISABLED_LIGHT_COLOR if self.loading or self.api.sync_notifiers != 0 else False
        )
        self.doc_view()

    @property
    def loading(self):
        loader: 'Loader' = self.parent_context.screens.queue[0]
        return loader.files_to_load is not None or \
            loader.loading_feedback or \
            self.file_sync_operation and not self.file_sync_operation.finished

    def post_loop(self):
        # Draw progress bar for file sync operations
        if self.file_sync_operation and not self.file_sync_operation.finished:
            draw_bottom_loading_bar(self.parent_context, self.file_sync_operation.done, self.file_sync_operation.total)
            return

        # Draw sync operation from loader
        loader: 'Loader' = self.parent_context.screens.queue[0]  # The loader is always the first screen
        if loader.files_to_load is not None:
            draw_bottom_loading_bar(self.parent_context, loader.files_loaded, loader.files_to_load)
            # Update the data if the loader has loaded more files
            if loader.loading_feedback + 3 < loader.files_loaded:
                self.get_items()
                loader.loading_feedback = loader.files_loaded
        elif loader.loading_feedback:
            self.get_items()
            loader.loading_feedback = 0
        elif time.time() - loader.loading_complete_marker < 1:  # For 1 second after loading is complete
            draw_bottom_loading_bar(self.parent_context, 1, 1, finish=True)

    def _critical_event_hook(self, event):
        if isinstance(event, ResizeEvent):
            self.invalidate_cache()
            self.bar.handle_scales()
            self.side_bar.handle_scales()
            self.doc_view.update_size()
        elif isinstance(event, NewDocuments):
            self.get_items()

    def _non_critical_event_hook(self, event):
        if isinstance(event, FileSyncProgress):
            self.file_sync_operation = event
        elif isinstance(event, DocumentSyncProgress):
            self.document_sync_operations[event.document_uuid] = event

    def api_event_hook(self, event):
        self._non_critical_event_hook(event)
        with self.call_lock:
            self._critical_event_hook(event)

    def invalidate_cache(self):
        header_texts = {key: text for key, text in self.texts.items() if
                        key in self.MAINTAIN_TEXT_KEYS}
        self.texts.clear()
        self.texts.update(header_texts)
        self.get_items()
        self.rect_calculations()
        get_bottom_bar_rect.cache_clear()

    def rect_calculations(self):
        # Handle sync refresh button rect
        self.resync_icon = self.icons['rotate']
        self.resync_rect = pe.Rect(0, 0, *self.resync_icon.size)
        padded = self.resync_rect.copy()
        padded.size = (self.ratios.main_menu_top_height,) * 2
        padded.topright = (self.width, 0)
        self.resync_rect.center = padded.center

    def handle_event(self, event):
        self.doc_view.handle_event(event)

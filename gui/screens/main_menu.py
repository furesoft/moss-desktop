import time
from functools import lru_cache
from queue import Queue
from threading import Lock
from typing import TYPE_CHECKING, Dict, List, Union

import pygameextra as pe

from gui.cloud_action_helper import import_files_to_cloud
from gui.events import ResizeEvent
from gui.file_prompts import import_prompt
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


class TopBar(pe.ChildContext):
    LAYER = pe.AFTER_LOOP_LAYER
    BUTTONS = (
        {
            "text": "Notebook",
            "icon": "notebook_add",
            "action": 'create_notebook',
        }, {
            "text": "Folder",
            "icon": "folder_add",
            "action": 'create_collection',
        }, {
            "text": "Import",
            "icon": "import",
            "action": 'import_action'
        }, {
            "text": "Export",
            "icon": "export",
            "action": None,
            "disabled": True
        },
    )

    # definitions from GUI
    icons: Dict[str, pe.Image]
    ratios: 'Ratios'

    # Scaled button texts
    texts: List[pe.Text]

    def __init__(self, parent: 'MainMenu'):
        self.texts = []
        self.main_menu = parent
        super().__init__(parent.parent_context)
        self.handle_scales()

    @property
    @lru_cache()
    def buttons(self) -> List[pe.RectButton]:
        width = 0
        buttons: List[pe.RectButton] = []
        for i, button in enumerate(self.BUTTONS):
            icon = self.icons[button['icon']]
            rect = pe.Rect(
                0, 0,
                self.texts[i].rect.width + icon.width * 1.5,
                self.ratios.main_menu_top_height
            )
            rect.inflate_ip(self.ratios.main_menu_x_padding, -self.ratios.main_menu_x_padding)
            disabled = button.get('disabled', False)
            buttons.append((
                pe.RectButton(
                    rect,
                    Defaults.TRANSPARENT_COLOR,
                    Defaults.BUTTON_ACTIVE_COLOR,
                    action_set={
                        'l_click': {
                            'action': getattr(self, button['action']) if button['action'] else None
                        },
                        'hover_draw': None,
                        'hover': None
                    },
                    disabled=disabled,
                    name=f'main_menu.top_bar.button_{i}'
                )
            ))
            width += buttons[-1].area.width
        width += (len(self.BUTTONS) - 1) * self.ratios.main_menu_bar_padding
        x = self.width / 2
        x -= width / 2
        for button in buttons:
            button.area.left = x
            x = button.area.right + self.ratios.main_menu_bar_padding

        return buttons

    @property
    def button_data_zipped(self):
        return zip(self.buttons, self.BUTTONS, self.texts)

    def handle_scales(self):
        # Cache reset
        self.texts.clear()
        self.__class__.buttons.fget.cache_clear()

        # Handle texts so we know their size
        for button_meta in self.BUTTONS:
            self.texts.append(pe.Text(
                button_meta['text'], Defaults.MAIN_MENU_BAR_FONT, self.ratios.main_menu_bar_size,
                colors=Defaults.TEXT_COLOR_T
            ))

        # Process final text and icon positions inside button and padding
        for button, button_meta, button_text in self.button_data_zipped:
            # Position the button text with padding
            button_text.rect.midright = button.area.midright
            button_text.rect.right -= self.ratios.main_menu_x_padding / 2

            # Position the icon with padding
            icon = self.icons[button_meta['icon']]
            icon_rect = pe.Rect(0, 0, *icon.size)
            icon_rect.midleft = button.area.midleft
            icon_rect.left += self.ratios.main_menu_x_padding / 2
            button_meta['icon_rect'] = icon_rect

    def loop(self):
        for button, button_meta, button_text in self.button_data_zipped:
            pe.settings.game_context.buttons.append(button)
            pe.button.check_hover(button)
            button_text.display()

            icon = self.icons[button_meta['icon']]
            icon.display(button_meta['icon_rect'].topleft)

            if button.disabled:
                pe.draw.rect(Defaults.BUTTON_DISABLED_LIGHT_COLOR, button.area)

    def create_notebook(self):
        NameFieldScreen(self.parent_context, "New Notebook", "", self._create_notebook, None, submit_text='Create notebook')

    def create_collection(self):
        NameFieldScreen(self.parent_context, "New Folder", "", self._create_collection, None, submit_text='Create folder')

    def _create_notebook(self, title):
        doc = Document.new_notebook(self.api, title, self.main_menu.navigation_parent)
        self.api.upload(doc)
    
    def _create_collection(self, title):
        col = DocumentCollection.create(self.api, title, self.main_menu.navigation_parent)
        self.api.upload(col)

    def import_action(self):
        import_prompt(lambda file_paths: import_files_to_cloud(self.parent_context, file_paths))


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
        'trash': "Trash"
    }

    file_sync_operation: Union[None, FileSyncProgress]

    resync_icon: pe.Image
    resync_rect: pe.Rect
    doc_view: MainMenuDocView

    def __init__(self, parent: 'GUI'):
        self.navigation_parent = parent.config.last_opened_folder
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
        for key, text in self.HEADER_TEXTS.items():
            self.texts[key] = pe.Text(text, Defaults.MAIN_MENU_FONT, self.ratios.main_menu_my_files_size,
                                      (0, 0), Defaults.TEXT_COLOR)
            self.texts[key].rect.topleft = (
                self.ratios.main_menu_x_padding, self.ratios.main_menu_top_height + self.ratios.main_menu_top_padding)

        self.doc_view = MainMenuDocView(parent)
        self.get_items()

        self.document_sync_operations: Dict[str, DocumentSyncProgress] = {}
        self.rect_calculations()

    @property
    def view_mode(self):
        return self.config.main_menu_view_mode

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

                parent = document_collections[parent].parent
        self.doc_view.handle_texts()

    def pre_loop(self):
        if 'screenshot' in self.icons:
            self.icons['screenshot'].display()

    def set_parent(self, uuid=None):
        self.navigation_parent = uuid
        if self.config.save_last_opened_folder and self.config.last_opened_folder != uuid:
            self.config.last_opened_folder = uuid
            self.parent_context.dirty_config = True
        self.get_items()
        self.quick_refresh()

    @staticmethod
    def get_sorted_document_collections(old_document_collections) -> sorted:
        return sorted(old_document_collections, key=lambda item: item.metadata.visible_name)

    def get_sorted_documents(self, original_documents_list: List['Document']) -> Union[List['Document'], reversed]:
        documents = sorted(original_documents_list, key=self.SORTING_FUNCTIONS[self.current_sorting_mode])
        if self.current_sorting_reverse:
            return reversed(documents)
        return documents

    def refresh(self):
        self.api.spread_event(SyncRefresh())

    def loop(self):
        pe.draw.line(Defaults.LINE_GRAY, (0, self.ratios.main_menu_top_height),
                     (self.width, self.ratios.main_menu_top_height), self.ratios.line)

        render_header(self.parent_context, self.texts, self.set_parent, self.path_queue)

        self.resync_icon.display(self.resync_rect.topleft)
        pe.button.rect(
            self.ratios.pad_button_rect(self.resync_rect),
            Defaults.TRANSPARENT_COLOR, Defaults.BUTTON_ACTIVE_COLOR,
            action=self.refresh, name='main_menu.refresh'
        )

        self.doc_view()

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
        header_texts = {key: text for key, text in self.texts.items() if key in self.HEADER_TEXTS}
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

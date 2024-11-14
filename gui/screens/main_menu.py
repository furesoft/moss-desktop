from functools import lru_cache
from queue import Queue
from threading import Lock
from typing import TYPE_CHECKING, Dict, List

import pygameextra as pe

from gui.events import ResizeEvent, InternalSyncCompleted
from gui.file_prompts import import_prompt
from rm_api.notifications.models import SyncRefresh

from gui.defaults import Defaults
from gui.helpers import shorten_path, shorten_folder, shorten_document, shorten_folder_by_size
from gui.rendering import render_button_using_text, render_document, render_collection, render_header, \
    draw_bottom_loading_bar

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
            "action": None,
            "disabled": True
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
        super().__init__(parent)
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
                    Defaults.TRANSPARENT_COLOR if disabled else (0, 0, 0, 0),
                    Defaults.BUTTON_ACTIVE_COLOR,
                    action=getattr(self, button['action']) if button['action'] else None,
                    disabled=disabled
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

    def import_action(self):
        # TODO: Make it actually import
        import_prompt(print)


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

    def __init__(self, parent: 'GUI'):
        self.navigation_parent = parent.config.last_opened_folder
        self.document_collections = {}
        self.documents = {}
        self.texts: Dict[str, pe.Text] = {}
        self.path_queue = Queue()
        self.call_lock = Lock()
        self.bar = TopBar(parent)
        parent.api.add_hook("main_menu_cache_invalidator", self.api_event_hook)
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

    @property
    def view_mode(self):
        return self.config.main_menu_view_mode

    def __call__(self, *args, **kwargs):
        with self.call_lock:
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

        # Preparing the document collection texts
        for uuid, document_collection in document_collections.items():
            if self.texts.get(uuid) is None or self.texts[
                uuid + '_full'
            ].text != document_collection.metadata.visible_name:
                if self.view_mode == 'list':
                    shortened_text = shorten_folder_by_size(document_collection.metadata.visible_name, self.width)
                else:
                    shortened_text = shorten_folder(document_collection.metadata.visible_name)
                self.texts[uuid] = pe.Text(shortened_text,
                                           Defaults.FOLDER_FONT,
                                           self.ratios.main_menu_label_size, (0, 0), Defaults.TEXT_COLOR)
                self.texts[uuid + '_full'] = pe.Text(document_collection.metadata.visible_name,
                                                     Defaults.FOLDER_FONT,
                                                     self.ratios.main_menu_label_size, (0, 0), Defaults.TEXT_COLOR)

        # Preparing the document texts
        for uuid, document in documents.items():
            if self.texts.get(uuid) is None or self.texts[uuid + '_full'].text != document.metadata.visible_name:
                self.texts[uuid] = pe.Text(shorten_document(document.metadata.visible_name),
                                           Defaults.DOCUMENT_TITLE_FONT,
                                           self.ratios.main_menu_document_title_size, (0, 0),
                                           Defaults.DOCUMENT_TITLE_COLOR)
                self.texts[uuid + '_full'] = pe.Text(document.metadata.visible_name,
                                                     Defaults.DOCUMENT_TITLE_FONT,
                                                     self.ratios.main_menu_document_title_size, (0, 0),
                                                     Defaults.DOCUMENT_TITLE_COLOR)

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

    def get_sorted_document_collections(self):
        return sorted(self.document_collections.values(), key=lambda item: item.metadata.visible_name)

    def get_sorted_documents(self):
        documents = sorted(self.documents.values(), key=self.SORTING_FUNCTIONS[self.current_sorting_mode])
        if self.current_sorting_reverse:
            return reversed(documents)
        return documents

    def refresh(self):
        self.api.spread_event(SyncRefresh())

    def loop(self):
        pe.draw.line(Defaults.LINE_GRAY, (0, self.ratios.main_menu_top_height),
                     (self.width, self.ratios.main_menu_top_height), self.ratios.pixel(2))

        render_header(self.parent_context, self.texts, self.set_parent, self.path_queue)

        x = self.ratios.main_menu_x_padding
        y = self.texts['my_files'].rect.bottom + self.ratios.main_menu_my_files_folder_padding

        # Rendering the folders
        document_collection_width = \
            self.ratios.main_menu_document_width if self.view_mode == 'grid' else self.width - x * 2
        for i, document_collection in enumerate(self.get_sorted_document_collections()):
            render_collection(self.parent_context, document_collection, self.texts,
                              self.set_parent, x, y, document_collection_width)

            if self.view_mode == 'grid':
                x += self.ratios.main_menu_document_width + self.ratios.main_menu_document_padding
                if x + self.ratios.main_menu_document_width > self.width and i + 1 < len(self.document_collections):
                    x = self.ratios.main_menu_x_padding
                    y += self.ratios.main_menu_folder_height_distance
            else:
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
            if x + self.ratios.main_menu_document_width > self.width and i + 1 < len(self.documents):
                x = self.ratios.main_menu_x_padding
                y += self.ratios.main_menu_document_height + self.ratios.main_menu_document_height_distance
        if self.config.debug:
            pe.button.rect((0, 0, self.ratios.main_menu_top_height, self.ratios.main_menu_top_height), (0, 0, 0, 20),
                           (255, 0, 0, 50), action=self.refresh)

    def post_loop(self):
        loader: 'Loader' = self.parent_context.screens.queue[0]
        if loader.files_to_load is not None:
            draw_bottom_loading_bar(self.parent_context, loader.files_loaded, loader.files_to_load)
            # Update the data if the loader has loaded more files
            if loader.loading_feedback + 3 < loader.files_loaded:
                self.get_items()
                loader.loading_feedback = loader.files_loaded
        elif loader.loading_feedback:
            self.get_items()
            loader.loading_feedback = 0

    def _critical_event_hook(self, event):
        if isinstance(event, ResizeEvent):
            self.invalidate_cache()
            self.bar.handle_scales()
        elif isinstance(event, InternalSyncCompleted):
            self.get_items()

    def api_event_hook(self, event):
        with self.call_lock:
            self._critical_event_hook(event)

    def invalidate_cache(self):
        my_files_text = self.texts['my_files']
        self.texts.clear()
        self.texts['my_files'] = my_files_text
        self.get_items()

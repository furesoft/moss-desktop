import os
import threading
import time
from traceback import print_exc

import pygameextra as pe
from typing import TYPE_CHECKING, Union, Dict

from gui.screens.mixins import LogoMixin
from rm_api.notifications.models import SyncCompleted, NewDocuments
from gui.defaults import Defaults
from gui.screens.main_menu import MainMenu

if TYPE_CHECKING:
    from gui.gui import GUI
    from rm_api import API


class ReusedIcon:
    def __init__(self, key: str, scale: float):
        self.key = key
        self.scale = scale


class ResizedIcon:
    def __init__(self, item: str, scale: float):
        self.item = item
        self.scale = scale


class Loader(pe.ChildContext, LogoMixin):
    TO_LOAD = {
        # Icons and Images
        'folder': os.path.join(Defaults.ICON_DIR, 'folder.svg'),
        'folder_inverted': os.path.join(Defaults.ICON_DIR, 'folder_inverted.svg'),
        'folder_add': os.path.join(Defaults.ICON_DIR, 'folder_add.svg'),
        'folder_add_inverted': os.path.join(Defaults.ICON_DIR, 'folder_add_inverted.svg'),
        'folder_empty': os.path.join(Defaults.ICON_DIR, 'folder_empty.svg'),
        'folder_empty_inverted': os.path.join(Defaults.ICON_DIR, 'folder_empty_inverted.svg'),
        'star': os.path.join(Defaults.ICON_DIR, 'star.svg'),
        'star_inverted': os.path.join(Defaults.ICON_DIR, 'star_inverted.svg'),
        'star_empty': os.path.join(Defaults.ICON_DIR, 'star_empty.svg'),
        'star_empty_inverted': os.path.join(Defaults.ICON_DIR, 'star_empty_inverted.svg'),
        'tag': os.path.join(Defaults.ICON_DIR, 'tag.svg'),
        'tag_inverted': os.path.join(Defaults.ICON_DIR, 'tag_inverted.svg'),
        'chevron_down': os.path.join(Defaults.ICON_DIR, 'chevron_down.svg'),
        'chevron_down_inverted': os.path.join(Defaults.ICON_DIR, 'chevron_down_inverted.svg'),
        'chevron_right': os.path.join(Defaults.ICON_DIR, 'chevron_right.svg'),
        'chevron_right_inverted': os.path.join(Defaults.ICON_DIR, 'chevron_right_inverted.svg'),
        'small_chevron_down': os.path.join(Defaults.ICON_DIR, 'small_chevron_down.svg'),
        'small_chevron_down_inverted': os.path.join(Defaults.ICON_DIR, 'small_chevron_down_inverted.svg'),
        'small_chevron_right': os.path.join(Defaults.ICON_DIR, 'small_chevron_right.svg'),
        'small_chevron_right_inverted': os.path.join(Defaults.ICON_DIR, 'small_chevron_right_inverted.svg'),
        'cloud': os.path.join(Defaults.ICON_DIR, 'cloud.svg'),
        'cloud_download': os.path.join(Defaults.ICON_DIR, 'cloud_download.svg'),
        'cloud_synced': os.path.join(Defaults.ICON_DIR, 'cloud_synced.svg'),
        'cloud_synced_inverted': os.path.join(Defaults.ICON_DIR, 'cloud_synced_inverted.svg'),
        'warning_circle': os.path.join(Defaults.ICON_DIR, 'warning_circle.svg'),
        'notebook_large': os.path.join(Defaults.ICON_DIR, 'notebook_large.svg'),
        'notebook': ReusedIcon('notebook_large', 0.333),
        'notebook_add': os.path.join(Defaults.ICON_DIR, 'notebook_add.svg'),
        'share': os.path.join(Defaults.ICON_DIR, 'share.svg'),
        'export': os.path.join(Defaults.ICON_DIR, 'export.svg'),
        'import': os.path.join(Defaults.ICON_DIR, 'import.svg'),
        'info': os.path.join(Defaults.ICON_DIR, 'information_circle.svg'),
        'rotate': os.path.join(Defaults.ICON_DIR, 'rotate.svg'),
        'rotate_inverted': os.path.join(Defaults.ICON_DIR, 'rotate_inverted.svg'),
        'burger': os.path.join(Defaults.ICON_DIR, 'burger.svg'),
        'burger_inverted': os.path.join(Defaults.ICON_DIR, 'burger_inverted.svg'),
        'filter': os.path.join(Defaults.ICON_DIR, 'filter.svg'),
        'context_menu': os.path.join(Defaults.ICON_DIR, 'context_menu.svg'),
        'pencil': os.path.join(Defaults.ICON_DIR, 'pencil.svg'),
        'my_files': os.path.join(Defaults.ICON_DIR, 'my_files.svg'),
        'my_files_inverted': os.path.join(Defaults.ICON_DIR, 'my_files_inverted.svg'),
        'trashcan': os.path.join(Defaults.ICON_DIR, 'trashcan.svg'),
        'trashcan_inverted': os.path.join(Defaults.ICON_DIR, 'trashcan_inverted.svg'),
        'trashcan_delete': os.path.join(Defaults.ICON_DIR, 'trashcan_delete.svg'),
        'trashcan_delete_inverted': os.path.join(Defaults.ICON_DIR, 'trashcan_delete_inverted.svg'),
        'cog': os.path.join(Defaults.ICON_DIR, 'cog.svg'),
        'cog_inverted': os.path.join(Defaults.ICON_DIR, 'cog_inverted.svg'),
        'heart': os.path.join(Defaults.ICON_DIR, 'heart.svg'),
        'compass': os.path.join(Defaults.ICON_DIR, 'compass.svg'),
        'compass_inverted': os.path.join(Defaults.ICON_DIR, 'compass_inverted.svg'),
        'duplicate': os.path.join(Defaults.ICON_DIR, 'duplicate.svg'),
        'duplicate_inverted': os.path.join(Defaults.ICON_DIR, 'duplicate_inverted.svg'),
        'text_edit': os.path.join(Defaults.ICON_DIR, 'text_edit.svg'),
        'text_edit_inverted': os.path.join(Defaults.ICON_DIR, 'text_edit_inverted.svg'),
        'move': os.path.join(Defaults.ICON_DIR, 'move.svg'),
        'move_inverted': os.path.join(Defaults.ICON_DIR, 'move_inverted.svg'),
        'x_medium': os.path.join(Defaults.ICON_DIR, 'x_medium.svg'),
        'x_medium_inverted': os.path.join(Defaults.ICON_DIR, 'x_medium_inverted.svg'),
        'discord_qr_code': ResizedIcon(os.path.join(Defaults.IMAGES_DIR, 'discord_qr_code.png'), 0.1),

        # 'screenshot': 'Screenshot_20241023_162027.png',

        # Data files
        'light_pdf': os.path.join(Defaults.DATA_DIR, 'light.pdf')
    }

    LAYER = pe.AFTER_LOOP_LAYER
    icons: Dict[str, pe.Image]
    api: 'API'
    logo: pe.Text
    line_rect: pe.Rect

    def __init__(self, parent: 'GUI'):
        super().__init__(parent)
        self.initialize_logo_and_line()
        self.api.add_hook('loader_resize_check', self.resize_check_hook)
        self.items_loaded = 0
        self.files_loaded = 0
        self.loading_feedback = 0  # Used by main menu to know if enough changes have been made since last checked
        self.loading_complete_marker = 0  # A timestamp of last sync completion
        self.files_to_load: Union[int, None] = None
        self.last_progress = 0
        self.current_progress = 0
        self.initialized = False

    def start_syncing(self):
        threading.Thread(target=self.get_documents, daemon=True).start()

    def _load(self):
        for key, item in self.TO_LOAD.items():
            if isinstance(item, ReusedIcon):
                self.icons[key] = self.icons[item.key].copy()
                self.icons[key].resize(tuple(v * item.scale for v in self.icons[key].size))
            elif isinstance(item, ResizedIcon):
                self.load_image(key, item.item, item.scale)
            elif not isinstance(item, str):
                continue
            elif item.endswith('.svg'):
                # SVGs are 40px, but we use 1000px height, so they are 23px
                # 23 / 40 = 0.575
                # but, I find 0.5 to better match
                self.load_image(key, item, 0.5)
            elif item.endswith('.png'):
                self.load_image(key, item)

            else:
                self.load_data(key, item)
            self.items_loaded += 1

    def load(self):
        try:
            self._load()
        except:
            print_exc()

    def get_documents(self):
        def progress(loaded, to_load):
            self.files_loaded = loaded
            self.files_to_load = to_load

        self.loading_feedback = 0
        self.loading_complete_marker = 0
        self.api.get_documents(progress)
        if self.config.last_root != self.api.last_root:
            self.config.last_root = self.api.last_root
            self.parent_context.dirty_config = True
        self.files_to_load = None
        if not self.current_progress:
            self.current_progress = 1
        self.api.spread_event(NewDocuments())

        self.loading_complete_marker = time.time()

    def load_image(self, key, file, multiplier: float = 1):
        self.icons[key] = pe.Image(file)
        self.icons[key].resize(tuple(self.ratios.pixel(v * multiplier) for v in self.icons[key].size))

    def load_data(self, key, file):
        with open(file, 'rb') as f:
            self.data[key] = f.read()

    def progress(self):
        if self.files_to_load is None and self.config.wait_for_everything_to_load and not self.current_progress:
            # Before we know the file count, just return 0 progress
            return 0
        try:
            if not self.config.wait_for_everything_to_load:
                self.current_progress = self.items_loaded / len(self.TO_LOAD)
            else:
                self.current_progress = (
                                                self.items_loaded +
                                                self.files_loaded
                                        ) / (
                                                len(self.TO_LOAD) +
                                                (self.files_to_load or self.files_loaded)
                                        )
        except ZeroDivisionError:
            self.current_progress = 0
        self.last_progress = self.last_progress + (self.current_progress - self.last_progress) / (self.FPS * .1)
        if self.last_progress > .98:
            self.last_progress = 1
        elif not self.config.wait_for_everything_to_load and self.current_progress == 1 and self.last_progress < 0.9:
            self.last_progress = 0.9
        return self.last_progress

    def loop(self):
        self.logo.display()
        progress = self.progress()
        if progress:
            pe.draw.rect(Defaults.LINE_GRAY, self.line_rect, self.ratios.loader_loading_bar_thickness,
                         edge_rounding=self.ratios.loader_loading_bar_rounding)
            progress_rect = self.line_rect.copy()
            progress_rect.width *= progress
            if self.config.debug:
                icons_rect = self.line_rect.copy()
                icons_rect.width *= (self.items_loaded / len(self.TO_LOAD))
                pe.draw.rect(Defaults.LINE_GRAY_LIGHT, icons_rect, self.ratios.loader_loading_bar_thickness * 3,
                             edge_rounding=self.ratios.loader_loading_bar_rounding)
            pe.draw.rect(Defaults.SELECTED, progress_rect, 0, edge_rounding=self.ratios.loader_loading_bar_rounding)

    def post_loop(self):
        if self.current_progress == 1 and self.last_progress == 1:
            self.screens.put(MainMenu(self.parent_context))
            self.api.connect_to_notifications()
            self.api.add_hook('loader', self.loader_hook)

    def loader_hook(self, event):
        if isinstance(event, SyncCompleted):
            self.start_syncing()

    def pre_loop(self):
        if not self.initialized:
            threading.Thread(target=self.load, daemon=True).start()
            self.start_syncing()
            self.initialized = True

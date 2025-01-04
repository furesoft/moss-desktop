import atexit
import json
import os
import time
from numbers import Number
from os import makedirs
from typing import TypedDict, Union, TYPE_CHECKING

import appdirs
import pygameextra as pe
from queue import Queue
from box import Box
from colorama import Fore

from rm_api.auth import FailedToRefreshToken
from rm_api.notifications.models import APIFatal
from .events import ResizeEvent
from .literals import PDF_RENDER_MODES, NOTEBOOK_RENDER_MODES, MAIN_MENU_MODES, MAIN_MENU_LOCATIONS

Defaults = None

try:
    from CEF4pygame import CEFpygame
except Exception:
    CEFpygame = None
try:
    import pymupdf
except Exception:
    pymupdf = None

from rm_api import API
from .aspect_ratio import Ratios

if TYPE_CHECKING:
    from gui.screens.main_menu import MainMenu
    from .screens.import_screen import ImportScreen

pe.init()

AUTHOR = "RedTTG"
APP_NAME = "Moss"
INSTALL_DIR = appdirs.site_data_dir(APP_NAME, AUTHOR)
USER_DATA_DIR = appdirs.user_data_dir(APP_NAME, AUTHOR)
pe.settings.raise_error_for_button_without_name = True


class ConfigDict(TypedDict):
    enable_fake_screen_refresh: bool
    wait_for_everything_to_load: bool
    uri: str
    discovery_uri: str
    last_root: Union[None, str]
    last_guide: str
    pdf_render_mode: PDF_RENDER_MODES
    notebook_render_mode: NOTEBOOK_RENDER_MODES
    download_everything: bool
    download_last_opened_page_to_make_preview: bool
    save_last_opened_folder: bool
    last_opened_folder: Union[None, str]
    last_prompt_directory: Union[None, str]
    scale: Number
    doc_view_scale: Number
    main_menu_view_mode: MAIN_MENU_MODES
    main_menu_menu_location: MAIN_MENU_LOCATIONS
    format_raw_exports: bool
    add_ext_to_raw_exports: bool
    debug: bool
    portable_mode: bool


DEFAULT_CONFIG: ConfigDict = {
    'enable_fake_screen_refresh': False,
    'wait_for_everything_to_load': False,
    'uri': 'https://webapp.cloud.remarkable.com/',
    'discovery_uri': 'https://service-manager-production-dot-remarkable-production.appspot.com/',
    'last_root': None,
    'last_guide': 'welcome',
    'pdf_render_mode': 'pymupdf',
    'notebook_render_mode': 'rm_lines_svg_inker',
    'download_everything': False,
    'download_last_opened_page_to_make_preview': False,
    'save_last_opened_folder': True,
    'last_opened_folder': None,
    'last_prompt_directory': None,
    'scale': .9,
    'doc_view_scale': 1,
    'main_menu_view_mode': 'grid',
    'main_menu_menu_location': 'my_files',
    'format_raw_exports': True,
    'add_ext_to_raw_exports': True,
    'debug': False,
    'debug_button_rects': False,
    'portable_mode': False
}

ConfigType = Box[ConfigDict]


def load_config() -> ConfigType:
    config = DEFAULT_CONFIG
    changes = False

    try:
        # noinspection PyUnresolvedReferences
        i_am_an_install = os.path.exists(os.path.join(__compiled__.containing_dir, 'installed'))
    except NameError:
        i_am_an_install = os.path.exists(os.path.join(os.path.dirname(__file__), 'installed'))

    if i_am_an_install:
        file = os.path.join(USER_DATA_DIR, 'config.json')
    else:
        try:
            # noinspection PyUnresolvedReferences
            file = os.path.join(__compiled__.containing_dir, 'config.json')
        except NameError:
            file = 'config.json'

    setattr(pe.settings, 'config_file_path', file)

    # Ensure config directory path exists
    if base_dir := os.path.dirname(file):
        os.makedirs(base_dir, exist_ok=True)

    if os.path.exists(file):
        exists = True
        with open(file) as f:
            current_json = json.load(f)
            # Check if there are any new keys
            changes = len(config.keys() - current_json.keys()) != 0
            config = {**config, **current_json}
    else:
        changes = True
        exists = False
    if changes:
        with open(file, "w") as f:
            json.dump(config, f, indent=4)
        if not exists:
            print("Config file created. You can edit it manually if you want.")
    if config['pdf_render_mode'] not in PDF_RENDER_MODES.__args__:
        raise ValueError(f"Invalid pdf_render_mode: {config['pdf_render_mode']}")
    if config['pdf_render_mode'] == 'retry':
        config['pdf_render_mode'] = 'cef'
    if config['pdf_render_mode'] == 'cef' and CEFpygame is None:
        print(f"{Fore.YELLOW}Cef is not installed or is not compatible with your python version.{Fore.RESET}")
        config['pdf_render_mode'] = 'pymupdf'
    if config['pdf_render_mode'] == 'pymupdf' and not pymupdf:
        print(f"{Fore.YELLOW}PyMuPDF is not installed or is not compatible with your python version.{Fore.RESET}")
        config['pdf_render_mode'] = 'retry'
    return Box(config)


class GUI(pe.GameContext):
    ASPECT = 0.75
    HEIGHT = 1000
    WIDTH = int(HEIGHT * ASPECT)
    FPS = 60
    TITLE = f"{AUTHOR} {APP_NAME}"
    MODE = pe.display.DISPLAY_MODE_RESIZABLE
    FAKE_SCREEN_REFRESH_TIME = .1

    def __init__(self):
        global Defaults
        self.config = load_config()

        self.AREA = (self.WIDTH * self.config.scale, self.HEIGHT * self.config.scale)
        self.dirty_config = False
        self.screenshot = False

        atexit.register(self.save_config_if_dirty)
        setattr(pe.settings, 'config', self.config)
        setattr(pe.settings, 'indev', False)

        from .defaults import Defaults
        self.BACKGROUND = Defaults.BACKGROUND
        super().__init__()

        try:
            self.api = API(**self.api_kwargs)
        except FailedToRefreshToken:
            os.remove(Defaults.TOKEN_FILE_PATH)
            self.api = API(**self.api_kwargs)
        self.api.last_root = self.config.last_root
        self.api.debug = self.config.debug
        self.screens = Queue()
        self.ratios = Ratios(self.config.scale)
        self.icons = {}
        self.data = {}
        self.ctrl_hold = False
        self._import_screen: Union[ImportScreen, None] = None
        self.main_menu: Union['MainMenu', None] = None
        from gui.screens.version_checker import VersionChecker

        if self.api.token or self.api.offline_mode:
            from gui.screens.loader import Loader
            self.screens.put(Loader(self))
        else:
            from gui.screens.code_screen import CodeScreen
            self.screens.put(CodeScreen(self))
        if not pe.settings.indev and not self.config.debug and not self.config.portable_mode and not Defaults.INSTALLED:
            from gui.screens.installer import Installer
            self.screens.put(Installer(self))
        self.screens.put(VersionChecker(self))
        self.running = True
        self.doing_fake_screen_refresh = False
        self.reset_fake_screen_refresh = True
        self.fake_screen_refresh_timer: float = None
        self.original_screen_refresh_surface: pe.Surface = None
        self.fake_screen_refresh_surface: pe.Surface = None
        self.last_screen_count = 1
        self.api.add_hook('GUI', self.handle_api_event)
        pe.display.set_icon(Defaults.APP_ICON)
        makedirs(Defaults.THUMB_FILE_PATH, exist_ok=True)

    @property
    def api_kwargs(self):
        return {
            'require_token': False,
            'token_file_path': Defaults.TOKEN_FILE_PATH,
            'sync_file_path': Defaults.SYNC_FILE_PATH,
            'log_file': Defaults.LOG_FILE,
            'uri': self.config.uri,
            'discovery_uri': self.config.discovery_uri
        }

    def pre_loop(self):
        if self.config.enable_fake_screen_refresh and (len(
                self.screens.queue) != self.last_screen_count or not self.reset_fake_screen_refresh):
            self.doing_fake_screen_refresh = True
            if self.reset_fake_screen_refresh:
                self.fake_screen_refresh_timer = time.time()
            else:
                self.reset_fake_screen_refresh = True
            self.last_screen_count = len(self.screens.queue)
            smaller_size = tuple(v * .8 for v in self.size)

            self.original_screen_refresh_surface = pe.Surface(self.size)
            self.fake_screen_refresh_surface = pe.Surface(self.size,
                                                          surface=pe.pygame.Surface(self.size, flags=0))  # Non alpha

            self.original_screen_refresh_surface.stamp(self.surface)
            self.fake_screen_refresh_surface.stamp(self.surface.surface)

            # BLUR
            self.original_screen_refresh_surface.resize(smaller_size)
            self.original_screen_refresh_surface.resize(self.size)
            self.fake_screen_refresh_surface.resize(smaller_size)
            self.fake_screen_refresh_surface.resize(self.size)

            # Invert colors
            pixels = pe.pygame.surfarray.pixels2d(self.fake_screen_refresh_surface.surface)
            pixels ^= 2 ** 32 - 1
            del pixels

        super().pre_loop()

    def quick_refresh(self):
        self.reset_fake_screen_refresh = False
        self.fake_screen_refresh_timer = time.time() - self.FAKE_SCREEN_REFRESH_TIME * 5

    def loop(self):
        if not self.running:
            return
        self.screens.queue[-1]()

    def save_config(self):
        with open("config.json", "w") as f:
            json.dump(self.config, f, indent=4)

    def save_config_if_dirty(self):
        if not self.dirty_config:
            return
        self.save_config()

    def fake_screen_refresh(self):
        section = (time.time() - self.fake_screen_refresh_timer) / self.FAKE_SCREEN_REFRESH_TIME
        if section < 1:
            pe.fill.full(pe.colors.black)
            pe.display.blit(self.fake_screen_refresh_surface, (0, 0))
        elif section < 1.5:
            pe.fill.full(pe.colors.black)
        elif section < 2.5:
            self.screens.queue[-1]()
            self.doing_fake_screen_refresh = False
            self.reset_fake_screen_refresh = False
        elif section < 3.5:
            pe.display.blit(self.fake_screen_refresh_surface, (0, 0))
        elif section < 5:
            pe.fill.full(pe.colors.white)
        elif section < 5.5:
            pe.display.blit(self.original_screen_refresh_surface, (0, 0))
        else:
            del self.fake_screen_refresh_surface
            del self.original_screen_refresh_surface
            self.doing_fake_screen_refresh = False

    def post_loop(self):
        if len(self.screens.queue) == 0:
            self.running = False
            return

        if self.doing_fake_screen_refresh:
            self.fake_screen_refresh()

    def end_loop(self):
        if self.config.debug_button_rects:
            for button in self.buttons:
                rect = pe.Rect(*button.area)
                if button.display_reference.pos:
                    rect.x += button.display_reference.pos[0]
                    rect.y += button.display_reference.pos[1]
                pe.draw.rect((*pe.colors.red, 50), rect, 2)
        if self.screenshot:
            self.surface.save_to_file("screenshot.png")
            self.screenshot = False
        # A little memory leak check
        # print(sum(sys.getsizeof(document.content_data) for document in self.api.documents.values()))
        super().end_loop()

    @property
    def center(self):
        return self.width // 2, self.height // 2

    def extra_event(self, e):
        pass

    def handle_event(self, e: pe.event.Event):
        if pe.event.key_DOWN(pe.K_LCTRL) or pe.event.key_DOWN(pe.K_RCTRL):
            self.ctrl_hold = True
        elif pe.event.key_UP(pe.K_LCTRL) or pe.event.key_UP(pe.K_RCTRL):
            self.ctrl_hold = False
        if pe.event.resize_check():
            self.api.spread_event(ResizeEvent(pe.display.get_size()))
        if self.screens.queue[-1].handle_event != self.handle_event:
            self.screens.queue[-1].handle_event(e)
        if self.ctrl_hold and pe.event.key_DOWN(pe.K_s):
            self.screenshot = True
        self.extra_event(e)
        super().handle_event(e)

    def quit_check(self):
        self.running = False

    def handle_api_event(self, e):
        if isinstance(e, APIFatal):
            self.running = False
            self.api.log("A FATAL API ERROR OCCURRED, CRASHING!")
            raise AssertionError("A FATAL API ERROR OCCURRED, CRASHING!")

    @property
    def import_screen(self):
        if self._import_screen is not None:
            return self._import_screen
        from .screens.import_screen import ImportScreen
        self.screens.put(ImportScreen(self))
        return self.import_screen

    @import_screen.setter
    def import_screen(self, screen: Union['ImportScreen', None]):
        if screen is None:
            self._import_screen = None
        else:
            self._import_screen = screen

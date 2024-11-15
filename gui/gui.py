import atexit
import json
import os
import time
from numbers import Number
from typing import TypedDict, Literal, Union

import appdirs
import pygameextra as pe
from queue import Queue
from box import Box
from colorama import Fore

from rm_api.auth import FailedToRefreshToken
from .events import ResizeEvent

Defaults = None

try:
    from CEF4pygame import CEFpygame
except Exception:
    CEFpygame = None

from rm_api import API
from .aspect_ratio import Ratios

pe.init()

AUTHOR = "RedTTG"
APP_NAME = "Moss"
INSTALL_DIR = appdirs.site_data_dir(APP_NAME, AUTHOR)
USER_DATA_DIR = appdirs.user_data_dir(APP_NAME, AUTHOR)

MAIN_MENU_MODES = Literal['grid', 'list', 'compressed']
PDF_RENDER_MODES = Literal['cef', 'none']
NOTEBOOK_RENDER_MODES = Literal['rm_lines_svg_inker']


class ConfigDict(TypedDict):
    enable_fake_screen_refresh: bool
    wait_for_everything_to_load: bool
    uri: str
    discovery_uri: str
    pdf_render_mode: PDF_RENDER_MODES
    notebook_render_mode: NOTEBOOK_RENDER_MODES
    download_everything: bool
    download_last_opened_page_to_make_preview: bool
    save_last_opened_folder: bool
    last_opened_folder: Union[None, str]
    scale: Number
    main_menu_view_mode: MAIN_MENU_MODES
    format_raw_exports: bool
    add_ext_to_raw_exports: bool
    debug: bool
    portable_mode: bool


DEFAULT_CONFIG: ConfigDict = {
    'enable_fake_screen_refresh': True,
    # TODO: Fix the fact that disabling this, makes loading much slower
    'wait_for_everything_to_load': True,
    'uri': 'https://webapp.cloud.remarkable.com/',
    'discovery_uri': 'https://service-manager-production-dot-remarkable-production.appspot.com/',
    'pdf_render_mode': 'cef',
    'notebook_render_mode': 'rm_lines_svg_inker',
    'download_everything': False,
    'download_last_opened_page_to_make_preview': False,
    'save_last_opened_folder': False,
    'last_opened_folder': None,
    'scale': .9,
    'main_menu_view_mode': 'grid',
    'format_raw_exports': True,
    'add_ext_to_raw_exports': True,
    'debug': False,
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
    if config['pdf_render_mode'] == 'cef' and CEFpygame is None:
        print(f"{Fore.YELLOW}Cef is not installed or is not compatible with your python version.{Fore.RESET}")
        config['pdf_render_mode'] = 'none'
    return Box(config)


class GUI(pe.GameContext):
    ASPECT = 0.75
    HEIGHT = 1000
    WIDTH = int(HEIGHT * ASPECT)
    FPS = 60
    BACKGROUND = pe.colors.white
    TITLE = f"{AUTHOR} {APP_NAME}"
    MODE = pe.display.DISPLAY_MODE_RESIZABLE
    FAKE_SCREEN_REFRESH_TIME = .1

    def __init__(self):
        global Defaults
        self.config = load_config()

        self.AREA = (self.WIDTH * self.config.scale, self.HEIGHT * self.config.scale)
        self.dirty_config = False
        atexit.register(self.save_config_if_dirty)
        super().__init__()

        setattr(pe.settings, 'config', self.config)
        from .defaults import Defaults
        try:
            self.api = API(**self.api_kwargs)
        except FailedToRefreshToken:
            os.remove(Defaults.TOKEN_FILE_PATH)
            self.api = API(**self.api_kwargs)
        self.api.debug = self.config.debug
        self.screens = Queue()
        self.ratios = Ratios(self.config.scale)
        self.icons = {}
        if self.api.token:
            from gui.screens.loader import Loader
            self.screens.put(Loader(self))
        else:
            from gui.screens.code_screen import CodeScreen
            self.screens.put(CodeScreen(self))
        if not self.config.debug and not self.config.portable_mode and not Defaults.INSTALLED:
            from gui.screens.installer import Installer
            self.screens.put(Installer(self))
        self.running = True
        self.doing_fake_screen_refresh = False
        self.reset_fake_screen_refresh = True
        self.fake_screen_refresh_timer: float = None
        self.original_screen_refresh_surface: pe.Surface = None
        self.fake_screen_refresh_surface: pe.Surface = None
        self.last_screen_count = 1
        pe.display.set_icon(Defaults.APP_ICON)

    @property
    def api_kwargs(self):
        return {
            'require_token': False,
            'token_file_path': Defaults.TOKEN_FILE_PATH,
            'sync_file_path': Defaults.SYNC_FILE_PATH,
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

        if self.config.debug:
            for button in self.buttons:
                pe.draw.rect((*pe.colors.red, 50), button.area, 2)

        if self.doing_fake_screen_refresh:
            self.fake_screen_refresh()

    @property
    def center(self):
        return self.width // 2, self.height // 2

    def handle_event(self, e: pe.event.Event):
        if self.screens.queue[-1].handle_event != self.handle_event:
            self.screens.queue[-1].handle_event(e)
        if pe.event.quit_check():
            self.running = False
        if pe.event.resize_check():
            self.api.spread_event(ResizeEvent(pe.display.get_size()))

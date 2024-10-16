import json
import os
import time
from typing import TypedDict

import pygameextra as pe
from queue import Queue
from box import Box

from CEF4pygame import CEFpygame
from pygameextra import event

from rm_api import API
from .aspect_ratio import Ratios
from .loader import Loader
from .main_menu import MainMenu

pe.init()


class ConfigDict(TypedDict):
    enable_fake_screen_refresh: bool
    wait_for_everything_to_load: bool
    uri: str


DEFAULT_CONFIG: ConfigDict = {
    'enable_fake_screen_refresh': True,
    # TODO: Fix the fact that disabling this, makes loading much slower
    'wait_for_everything_to_load': True,
    'uri': 'https://webapp.cloud.remarkable.com/'
}


def load_config() -> Box[ConfigDict]:
    config = DEFAULT_CONFIG
    changes = False
    if os.path.exists("config.json"):
        exists = True
        with open("config.json") as f:
            current_json = json.load(f)
            # Check if there are any new keys
            changes = len(config.keys() - current_json.keys()) != 0
            config = {**config, **current_json}
    else:
        changes = True
        exists = False
    if changes:
        with open("config.json", "w") as f:
            json.dump(config, f, indent=4)
        if not exists:
            print("Config file created. You can edit it manually if you want.")
    return Box(config)


class GUI(pe.GameContext):
    ASPECT = 0.75
    HEIGHT = 1000
    WIDTH = int(HEIGHT * ASPECT)
    SCALE = .9
    FPS = 60
    BACKGROUND = pe.colors.white
    TITLE = "RedTTG rM GUI"
    FAKE_SCREEN_REFRESH_TIME = .1

    def __init__(self):
        self.AREA = (self.WIDTH * self.SCALE, self.HEIGHT * self.SCALE)
        super().__init__()
        self.api = API()
        self.screens = Queue()
        self.ratios = Ratios(self.SCALE)
        self.icons = {}
        self.config = load_config()
        self.api.uri = self.config.uri
        self.screens.put(Loader(self))
        self.running = True
        self.doing_fake_screen_refresh = False
        self.reset_fake_screen_refresh = True
        self.fake_screen_refresh_timer: float = None
        self.original_screen_refresh_surface: pe.Surface = None
        self.fake_screen_refresh_surface: pe.Surface = None
        self.last_screen_count = 1

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

    def post_loop(self):
        if len(self.screens.queue) == 0:
            self.running = False
            return
        if not self.doing_fake_screen_refresh:
            return

        # Fake screen refresh
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

    @property
    def center(self):
        return self.width // 2, self.height // 2

    def handle_event(self, e: pe.event.Event):
        if self.screens.queue[-1].handle_event != self.handle_event:
            self.screens.queue[-1].handle_event(e)
        if pe.event.quit_check():
            self.running = False

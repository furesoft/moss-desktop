import threading
import time
from queue import Queue

import pygameextra as pe
from pyperclip import paste as pyperclip_paste
from typing import TYPE_CHECKING

from rm_api.auth import FailedToGetToken
from .defaults import Defaults
from .loader import Loader, APP_NAME

if TYPE_CHECKING:
    from .gui import GUI


class CodeScreen(pe.ChildContext):
    LAYER = pe.AFTER_LOOP_LAYER
    CODE_LENGTH = 8
    BACKSPACE_DELETE_DELAY = 0.3  # Initial backspace delay
    BACKSPACE_DELETE_SPEED = 0.05  # After initial backspace delay

    parent_context: 'GUI'
    screens: Queue[pe.ChildContext]

    def __init__(self, parent: 'GUI'):
        super().__init__(parent)
        self.underscore = pe.Text(
            "_",
            Defaults.CODE_FONT, self.ratios.loader_logo_text_size,
            colors=Defaults.CODE_COLOR
        )
        self.underscore_red = pe.Text(
            "_",
            Defaults.CODE_FONT, self.ratios.loader_logo_text_size,
            colors=(Defaults.RED, None)
        )
        self.logo = pe.Text(
            APP_NAME,
            Defaults.LOGO_FONT, self.ratios.loader_logo_text_size,
            (
                self.width // 2,
                self.height // 2 - (self.underscore.rect.height + self.ratios.code_screen_header_padding // 2)
            ),
            Defaults.TEXT_COLOR_T
        )
        self.code_info = pe.Text(
            "Input your connect code",
            Defaults.LOGO_FONT, self.ratios.code_screen_info_size,
            colors=Defaults.TEXT_COLOR_T
        )
        self.code_info.rect.midtop = self.logo.rect.midbottom
        self.code_info.rect.y += self.ratios.code_screen_header_padding // 2
        self.underscore.rect.top = self.logo.rect.bottom + self.ratios.code_screen_header_padding
        self.underscore_red.rect.top = self.underscore.rect.top
        self.code = []
        self.code_text = []
        self.code_failed = False
        self.checking_code = False
        self.hold_backspace = False
        self.hold_backspace_timer = None
        self.ctrl_hold = False

    def add_character(self, char: str):
        if len(self.code) == self.CODE_LENGTH:
            return
        self.code.append(char)
        self.code_text.append(pe.Text(
            char,
            Defaults.CODE_FONT, self.ratios.loader_logo_text_size,
            colors=Defaults.TEXT_COLOR_T
        ))
        if len(self.code) == self.CODE_LENGTH:
            self.check_code()

    def handle_event(self, event):
        if event.type == pe.pygame.KEYDOWN:
            if self.ctrl_hold and event.key == pe.pygame.K_v:
                for char in pyperclip_paste():
                    if char.isalnum():
                        self.add_character(char)

            if event.key == pe.pygame.K_BACKSPACE and len(self.code) > 0:
                del self.code[-1]
                del self.code_text[-1]
                self.code_failed = False
                self.hold_backspace = True
                self.hold_backspace_timer = time.time() + self.BACKSPACE_DELETE_DELAY
            elif len(self.code) == self.CODE_LENGTH:
                pass
            elif event.key == pe.pygame.K_LCTRL or event.key == pe.pygame.K_RCTRL:
                self.ctrl_hold = True
            elif event.unicode.isalnum():
                self.add_character(event.unicode)
        elif event.type == pe.pygame.KEYUP:
            if event.key == pe.pygame.K_BACKSPACE:
                self.hold_backspace = False
            elif event.key == pe.pygame.K_LCTRL or event.key == pe.pygame.K_RCTRL:
                self.ctrl_hold = False


    def check_code(self):
        self.checking_code = True
        threading.Thread(target=self.check_code_thread, daemon=True).start()

    def check_code_thread(self):
        try:
            self.api.get_token("".join(self.code))
            self.screens.put(Loader(self.parent_context))
            del self.screens.queue[0]
        except FailedToGetToken:
            self.code_failed = True
        self.checking_code = False

    def pre_loop(self):
        # The background
        pe.fill.interlace(Defaults.LINE_GRAY, 5)

        # Handling backspace
        if self.hold_backspace and time.time() - self.hold_backspace_timer > self.BACKSPACE_DELETE_SPEED and len(
                self.code) > 0:
            self.hold_backspace_timer = time.time()
            del self.code[-1]
            del self.code_text[-1]

    def loop(self):
        self.logo.display()
        self.code_info.display()
        x = self.width // 2 - self.underscore.rect.width * (self.CODE_LENGTH / 2)
        x -= self.ratios.code_screen_spacing * (self.CODE_LENGTH - 1) / 2

        underscore = self.underscore_red if self.code_failed else self.underscore

        for i in range(self.CODE_LENGTH):
            underscore.rect.left = x
            underscore.display()
            if i < len(self.code):
                self.code_text[i].rect.midbottom = underscore.rect.midbottom
                self.code_text[i].display()
            x += underscore.rect.width + self.ratios.code_screen_spacing

    def post_loop(self):
        if not self.checking_code:
            return
        # Make a frozen paper effect
        pe.fill.transparency(pe.colors.white, 150)

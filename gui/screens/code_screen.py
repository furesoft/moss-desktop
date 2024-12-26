import os.path
import threading
import time
import webbrowser
from queue import Queue

import pygameextra as pe
from pyperclip import paste as pyperclip_paste
from typing import TYPE_CHECKING

from gui.events import ResizeEvent
from rm_api.auth import FailedToGetToken
from gui.defaults import Defaults
from gui.screens.loader import Loader
from gui.gui import APP_NAME

if TYPE_CHECKING:
    from gui.gui import GUI


class CodeScreen(pe.ChildContext):
    LAYER = pe.AFTER_LOOP_LAYER
    CODE_LENGTH = 8
    BACKSPACE_DELETE_DELAY = 0.3  # Initial backspace delay
    BACKSPACE_DELETE_SPEED = 0.05  # After initial backspace delay
    EVENT_HOOK_NAME = 'code_screen_resize_check'

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
            self.logo_position,
            Defaults.TEXT_COLOR_T
        )
        self.code_info = pe.Text(
            "Input your connect code",
            Defaults.LOGO_FONT, self.ratios.code_screen_info_size,
            colors=Defaults.TEXT_COLOR_T
        )
        self.website_info = pe.Text(
            self.config.uri.replace('https://', '').replace('http://', ''),
            Defaults.LOGO_FONT, self.ratios.code_screen_info_size,
            colors=Defaults.TEXT_COLOR_LINK if self.connecting_to_real_remarkable() else Defaults.TEXT_COLOR_T
        )
        self.share_icon = pe.Image(os.path.join(Defaults.ICON_DIR, 'share.svg'))
        self.update_code_text_positions()
        self.api.add_hook(self.EVENT_HOOK_NAME, self.resize_check_hook)
        self.code = []
        self.code_text = []
        self.code_failed = False
        self.checking_code = False
        self.hold_backspace = False
        self.hold_backspace_timer = None
        self.ctrl_hold = False

    @property
    def logo_position(self):
        return (
            self.width // 2,
            self.height // 2 - (self.underscore.rect.height + self.ratios.code_screen_header_padding // 2)
        )

    def update_code_text_positions(self):
        self.code_info.rect.midtop = self.logo.rect.midbottom
        self.code_info.rect.top += self.ratios.code_screen_header_padding // 2
        self.website_info.rect.centerx = self.code_info.rect.centerx
        self.underscore.rect.top = self.logo.rect.bottom + self.ratios.code_screen_header_padding
        self.underscore_red.rect.top = self.underscore.rect.top
        self.website_info.rect.bottom = self.underscore.rect.bottom + self.ratios.code_screen_header_padding

    def resize_check_hook(self, event):
        if isinstance(event, ResizeEvent):
            self.logo.rect.center = self.logo_position
            self.update_code_text_positions()

    def add_character(self, char: str):
        if len(self.code) == self.CODE_LENGTH:
            return
        self.code.append(char)
        self.code_text.append(pe.Text(
            char,
            Defaults.CODE_FONT, self.ratios.loader_logo_text_size,
            colors=Defaults.TEXT_COLOR_CODE
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
            self.api.remove_hook(self.EVENT_HOOK_NAME)
            del self.screens.queue[0]
        except FailedToGetToken:
            self.code_failed = True
        self.checking_code = False

    def pre_loop(self):
        # The background

        # Handling backspace
        if self.hold_backspace and time.time() - self.hold_backspace_timer > self.BACKSPACE_DELETE_SPEED and len(
                self.code) > 0:
            self.hold_backspace_timer = time.time()
            del self.code[-1]
            del self.code_text[-1]

    def connecting_to_real_remarkable(self):
        return 'remarkable.com' in self.config.uri

    def loop(self):
        self.logo.display()
        self.code_info.display()
        self.website_info.display()
        if self.connecting_to_real_remarkable():
            self.share_icon.display((
                self.website_info.rect.right + self.ratios.code_screen_spacing,
                self.website_info.rect.top + self.share_icon.height // 5
            ))
            pe.button.rect(
                self.ratios.pad_button_rect(self.website_info.rect),
                Defaults.TRANSPARENT_COLOR, Defaults.BUTTON_ACTIVE_COLOR,
                action=webbrowser.open,
                data=("https://my.remarkable.com/#desktop", 0, True),
                name='code_screen.webopen<rm>'
            )
        else:
            pe.button.rect(
                self.ratios.pad_button_rect(self.website_info.rect),
                Defaults.TRANSPARENT_COLOR, Defaults.BUTTON_ACTIVE_COLOR,
                action=webbrowser.open,
                data=(self.config.uri, 0, True),
                name='code_screen.webopen<custom>'
            )

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

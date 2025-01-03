from typing import TYPE_CHECKING

import pygameextra as pe

from gui.defaults import Defaults
from gui.events import ResizeEvent
from gui.rendering import render_button_using_text
from gui.screens.mixins import TitledMixin, ButtonReadyMixin

if TYPE_CHECKING:
    from gui import GUI


class Popup(pe.ChildContext, ButtonReadyMixin, TitledMixin):
    LAYER = pe.AFTER_LOOP_LAYER
    COLOR = (*Defaults.TRANSPARENT_COLOR[:3], 175)
    TITLE_COLORS = Defaults.TEXT_COLOR_H
    CLOSE_TEXT = "Close"
    BUTTON_TEXTS = {
        'close': "",
    }

    def __init__(self, parent: "GUI", title: str, description: str):
        super().__init__(parent)
        self.handle_title(title)
        self.BUTTON_TEXTS['close'] = self.CLOSE_TEXT
        self.handle_texts()
        self.description = pe.Text(description, Defaults.DEBUG_FONT, self.ratios.popup_description_size,
                                   colors=self.TITLE_COLORS)
        self.description.rect.left = self.title.rect.left
        self.description.rect.top = self.title.rect.bottom + self.ratios.popup_description_padding
        self.closed = False
        self.HOOK_ID = f'popup_{id(self)}_resize'
        self.api.add_hook(self.HOOK_ID, self.resize_check_hook)

    def close(self):
        self.closed = True
        self.api.remove_hook(self.HOOK_ID)

    def resize_check_hook(self, event):
        if isinstance(event, ResizeEvent):
            self.handle_texts()

    def loop(self):
        if self.closed:
            return
        pe.button.rect((0, 0, *self.size), self.COLOR, self.COLOR, name=f'popup_{id(self)}_background')
        pe.fill.interlace(Defaults.LINE_GRAY, 10)
        self.title.display()
        self.description.display()
        render_button_using_text(self.parent_context, self.texts['close'], outline=self.ratios.outline,
                                 inactive_color=Defaults.BACKGROUND,
                                 active_color=Defaults.BUTTON_ACTIVE_COLOR_INVERTED,
                                 action=self.close, name=f'popup_{id(self)}_close', text_infront=True)


class ConfirmPopup(Popup):
    CLOSE_TEXT = "Cancel"
    BUTTON_TEXTS = {
        'confirm': "Confirm",
        'close': "",
    }

    def __init__(self, parent: "GUI", title: str, description: str, confirm_action=None, cancel_action=None):
        super().__init__(parent, title, description)
        self.confirm_action = confirm_action
        self.cancel_action = cancel_action

    def _close(self):
        super().close()

    def close(self):
        if self.cancel_action:
            self.cancel_action()
        self._close()

    def ok(self):
        if self.confirm_action:
            self.confirm_action()
        self._close()

    def loop(self):
        super().loop()

        render_button_using_text(self.parent_context, self.texts['confirm'], outline=self.ratios.outline,
                                 inactive_color=Defaults.BACKGROUND,
                                 active_color=Defaults.BUTTON_ACTIVE_COLOR_INVERTED,
                                 action=self.ok, name=f'popup_{id(self)}_confirm', text_infront=True)


class WarningPopup(Popup):
    CLOSE_TEXT = "Close warning"

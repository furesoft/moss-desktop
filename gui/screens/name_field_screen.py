from typing import TYPE_CHECKING

import pygameextra as pe

from gui.defaults import Defaults
from gui.events import ResizeEvent
from gui.rendering import render_button_using_text
from gui.screens.mixins import TitledMixin, ButtonReadyMixin

if TYPE_CHECKING:
    from gui import GUI


class CustomInputBox(pe.InputBox):
    def __init__(self, gui: 'GUI', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gui = gui
        self._padding = gui.ratios.field_screen_input_padding

    def display(self):
        pe.draw.line(
            Defaults.LINE_GRAY,
            (self.area.left + self._padding, self.area.bottom),
            (self.area.right - self._padding, self.area.bottom),
            self.gui.ratios.line
        )
        super().display()

    def draw_cursor(self, active_blink: bool):
        if not active_blink:
            return
        pe.draw.line(Defaults.LINE_GRAY, (self.cursor_x, self.text.rect.top), (self.cursor_x, self.text.rect.bottom),
                     self.gui.ratios.line)


class NameFieldScreen(pe.ChildContext, ButtonReadyMixin, TitledMixin):
    LAYER = pe.AFTER_LOOP_LAYER

    field: pe.InputBox

    parent_context: 'GUI'

    BUTTON_TEXTS = {
        **ButtonReadyMixin.BUTTON_TEXTS,
    }

    EVENT_HOOK_NAME = 'name_field_screen_resize_check<{0}>'


    def __init__(self, gui: 'GUI', title, text, on_submit, on_cancel, empty_ok: bool = False):
        self.title = title
        self.empty_ok = empty_ok
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        self.has_focused = False
        super().__init__(gui)

        self.handle_title(title)
        self.handle_texts()

        self.field = CustomInputBox(
            gui,
            (0, self.title_bottom, self.width, gui.ratios.field_screen_input_height),
            Defaults.DOCUMENT_TITLE_FONT,
            text, gui.ratios.field_screen_input_size,
            colors=Defaults.DOCUMENT_TITLE_COLOR,
        )

        gui.screens.put(self)
        self.api.add_hook(self.EVENT_HOOK_NAME.format(id(self)), self.resize_check_hook)

    @property
    def text(self):
        return self.field.text.text

    def pre_loop(self):
        if not self.has_focused and not pe.mouse.clicked()[0]:
            self.field.focus()
            self.has_focused = True

    def close(self):
        self.api.remove_hook(self.EVENT_HOOK_NAME.format(id(self)))
        if self.on_cancel:
            self.on_cancel()
        del self.screens.queue[-1]

    def resize_check_hook(self, event):
        if isinstance(event, ResizeEvent):
            self.field.area.width = self.width
            self.calculate_texts()

    def loop(self):
        self.title.display()
        self.field.display()

        render_button_using_text(self.parent_context, self.texts['cancel'], outline=self.ratios.outline,
                                 action=self.close, name='import_screen.cancel',
                                 disabled=False if self.empty_ok or self.text else (0, 0, 0, 50))

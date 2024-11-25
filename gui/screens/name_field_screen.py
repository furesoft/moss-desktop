from typing import TYPE_CHECKING

import pygameextra as pe

from gui.defaults import Defaults

if TYPE_CHECKING:
    from gui import GUI


class CustomInputBox(pe.InputBox):
    def __init__(self, gui: 'GUI', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gui = gui

    def display(self):
        pe.draw.line(Defaults.LINE_GRAY, self.area.bottomleft, self.area.bottomright, self.gui.ratios.line)
        super().display()

    def draw_cursor(self, active_blink: bool):
        if not active_blink:
            return
        pe.draw.line(Defaults.LINE_GRAY, (self.cursor_x, self.text.rect.top), (self.cursor_x, self.text.rect.bottom),
                     self.gui.ratios.line)


class NameFieldScreen(pe.ChildContext):
    LAYER = pe.AFTER_LOOP_LAYER

    field: pe.InputBox

    def __init__(self, gui: 'GUI', title, text, on_submit, on_cancel):
        self.title = title
        self.text = text
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        super().__init__(gui)
        self.field = CustomInputBox(
            gui,
            (0, 0, self.width, gui.ratios.field_screen_input_height),
            Defaults.DOCUMENT_TITLE_FONT,
            text, gui.ratios.field_screen_input_size,
            colors=Defaults.DOCUMENT_TITLE_COLOR,
        )
        gui.screens.put(self)

    def loop(self):
        self.field.display()

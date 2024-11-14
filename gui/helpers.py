import pygameextra as pe
from typing import TYPE_CHECKING
from gui import APP_NAME
from gui.defaults import Defaults
from gui.events import ResizeEvent

if TYPE_CHECKING:
    from gui.aspect_ratio import Ratios


def shorten_name(name, letters=16, max_length=20):
    half = letters // 2
    # Account for the ellipsis
    one_short = half - 1
    two_short = half - 2
    if len(name) < max_length:
        return name
    if len(name) > letters:
        try:
            first, *mid, last = name.split(' ')
            if len(mid) > 1:
                i = 0
                while len(first) < half:
                    first += ' ' + mid[i]
                    i += 1
                    one_short += 1
                i = 1
                while len(last) < half:
                    last = mid[-i] + ' ' + last
                    i += 1
                    two_short += 2
        except ValueError:
            return f'{name[:two_short]}...{name[len(name) - two_short:]}'
        return f'{first[:one_short]}...{last[len(last) - two_short:]}'
    return name


def shorten_folder(name, letters=16, max_length=20):
    return shorten_name(name, letters, max_length)


def shorten_folder_by_size(name, width):
    max_length = width // 10
    letters = max_length - 4
    return shorten_name(name, letters, max_length)


def shorten_document(name, letters=20, max_length=24):
    return shorten_name(name, letters, max_length)


def shorten_path(path, letters=26, max_length=30):
    return shorten_name(path, letters)


class Logo:
    logo: pe.Text
    line_rect: pe.Rect
    big_line_rect: pe.Rect
    ratios: 'Ratios'
    width: int
    height: int

    def resize_check_hook(self, event):
        if isinstance(event, ResizeEvent):
            self.initialize_logo_and_line()

    def initialize_logo_and_line(self):
        self.logo = pe.Text(
            APP_NAME,
            Defaults.LOGO_FONT, self.ratios.loader_logo_text_size,
            pe.math.center(
                (
                    0, 0, self.width,
                    self.height - (
                            self.ratios.loader_loading_bar_height + self.ratios.loader_loading_bar_padding
                    )
                )
            ),
            Defaults.TEXT_COLOR
        )
        self.line_rect = pe.Rect(0, 0, self.ratios.loader_loading_bar_width,
                                 self.ratios.loader_loading_bar_height)
        self.line_rect.midtop = self.logo.rect.midbottom
        self.line_rect.top += self.ratios.loader_loading_bar_padding

        self.big_line_rect = pe.Rect(0, 0, self.ratios.loader_loading_bar_big_width,
                                 self.ratios.loader_loading_bar_big_height)
        self.big_line_rect.midtop = self.logo.rect.midbottom
        self.big_line_rect.top += self.ratios.loader_loading_bar_padding

from typing import TYPE_CHECKING

import pygameextra as pe

if TYPE_CHECKING:
    from gui import GUI


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


def check_width(text: str, font: pe.pygame.Font):
    metrics = font.metrics(text)
    x = 0
    for metric in metrics:
        x += metric[4]
    return x


def dynamic_text(name, font_filename, fontsize, width):
    font = pe.text.get_font(font_filename, fontsize)

    if check_width(name, font) <= width:
        return name

    center = len(name) // 2
    left = center
    right = center

    while check_width(name[:left] + '...' + name[right:], font) > width:
        left -= 1
        right += 1

    return name[:left] + '...' + name[right:]


def shorten_path(path, letters=26, max_length=30):
    return shorten_name(path, letters)


def invert_icon(gui: 'GUI', key: str, result_key: str):
    if key == result_key:
        pixels = pe.pygame.surfarray.pixels2d(gui.icons[key].surface.surface)
        pixels ^= 0x00FFFFFF
        del pixels
        return
    icon = gui.icons[key].copy()
    gui.icons[result_key] = icon
    invert_icon(gui, result_key, result_key)

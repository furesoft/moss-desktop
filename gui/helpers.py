import pygameextra as pe


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


def text_width(text, font, fontsize):
    return pe.Text(text, font, fontsize).rect.width


def text_width(text, font, fontsize):
    return pe.Text(text, font, fontsize).rect.width


def dynamic_text(name, font, fontsize, width):
    if text_width(name, font, fontsize) <= width:
        return name

    ellipsis = "..."
    max_length = len(name)
    start_length = max_length // 2
    end_length = max_length - start_length

    while start_length > 0 and end_length > 0:
        test_text = name[:start_length] + ellipsis + name[-end_length:]
        if text_width(test_text, font, fontsize) <= width:
            return test_text
        start_length -= 1
        end_length -= 1

    return ellipsis


def shorten_path(path, letters=26, max_length=30):
    return shorten_name(path, letters)

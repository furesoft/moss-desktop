import os.path
import pygameextra as pe


class Defaults:
    ASSET_DIR = "assets"
    HTML_DIR = os.path.join(ASSET_DIR, 'html')
    ICON_DIR = os.path.join(ASSET_DIR, 'icons')
    FONT_DIR = os.path.join(ASSET_DIR, 'fonts')

    CUSTOM_FONT = os.path.join(FONT_DIR, 'Imperator.ttf')
    CUSTOM_FONT_BOLD = os.path.join(FONT_DIR, 'Imperator Bold.ttf')
    FOLDER_FONT = os.path.join(FONT_DIR, 'Roboto-Medium.ttf')
    PATH_FONT = os.path.join(FONT_DIR, 'Roboto-Regular.ttf')
    DOCUMENT_TITLE_FONT = os.path.join(FONT_DIR, 'Roboto-Regular.ttf')
    DOCUMENT_ERROR_FONT = os.path.join(FONT_DIR, 'Roboto-Medium.ttf')

    LOGO_FONT = CUSTOM_FONT_BOLD
    MAIN_MENU_FONT = CUSTOM_FONT_BOLD

    TEXT_COLOR = (pe.colors.black, pe.colors.white)
    DOCUMENT_TITLE_COLOR = ((20, 20, 20), pe.colors.white)
    DOCUMENT_SUBTITLE_COLOR = ((100, 100, 100), pe.colors.white)
    TEXT_COLOR_T = (pe.colors.black, None)
    LINE_GRAY = (88, 88, 88)
    DOCUMENT_GRAY = (184, 184, 184)
    TRANSPARENT_COLOR = (0, 0, 0, 0)
    BUTTON_ACTIVE_COLOR = (0, 0, 0, 25)

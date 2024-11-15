import os.path
import sys
import __main__

from gui import USER_DATA_DIR

try:
    from cefpython3 import cefpython as cef
except Exception:
    cef = None
import pygameextra as pe


def get_asset_path():
    # Check if we are running in a Nuitka bundle
    if '__compiled__' in globals():
        if pe.settings.config.debug:
            print("Running as a Nuitka bundle")
        base_asset_dir = os.path.dirname(__main__.__file__)
        script_dir = __compiled__.containing_dir
    else:
        if pe.settings.config.debug:
            print("Running in development")
        base_asset_dir = os.path.abspath(".")
        script_dir = os.path.abspath(os.path.dirname(__main__.__file__))

    if pe.settings.config.debug:
        print(f"Base asset dir: {base_asset_dir}")
        print(f"Script dir: {script_dir}")
    return base_asset_dir, script_dir


class Defaults:
    BASE_ASSET_DIR, SCRIPT_DIR = get_asset_path()
    ASSET_DIR = os.path.join(BASE_ASSET_DIR, 'assets')
    INSTALLED = os.path.exists(os.path.join(BASE_ASSET_DIR, 'installed'))

    HTML_DIR = os.path.join(ASSET_DIR, 'html')
    ICON_DIR = os.path.join(ASSET_DIR, 'icons')
    FONT_DIR = os.path.join(ASSET_DIR, 'fonts')

    if INSTALLED:
        SCRIPT_DIR = USER_DATA_DIR
    TOKEN_FILE_PATH = os.path.join(SCRIPT_DIR, 'token')
    CONFIG_FILE_PATH = pe.settings.config_file_path  # The GUI handles the path for this
    SYNC_FILE_PATH = os.path.join(SCRIPT_DIR, 'sync')

    CUSTOM_FONT = os.path.join(FONT_DIR, 'Imperator.ttf')
    CUSTOM_FONT_BOLD = os.path.join(FONT_DIR, 'Imperator Bold.ttf')
    MONO_FONT = os.path.join(FONT_DIR, 'JetBrainsMono-Bold.ttf')
    ROBOTO_REGULAR_FONT = os.path.join(FONT_DIR, 'Roboto-Regular.ttf')
    ROBOTO_MEDIUM_FONT = os.path.join(FONT_DIR, 'Roboto-Medium.ttf')

    FOLDER_FONT = ROBOTO_MEDIUM_FONT
    PATH_FONT = ROBOTO_REGULAR_FONT
    DOCUMENT_TITLE_FONT = ROBOTO_REGULAR_FONT
    DOCUMENT_ERROR_FONT = ROBOTO_MEDIUM_FONT
    INSTALLER_FONT = ROBOTO_REGULAR_FONT

    LOGO_FONT = CUSTOM_FONT_BOLD
    MAIN_MENU_FONT = CUSTOM_FONT_BOLD
    MAIN_MENU_BAR_FONT = ROBOTO_MEDIUM_FONT
    CODE_FONT = MONO_FONT
    DEBUG_FONT = MONO_FONT

    TEXT_COLOR = (pe.colors.black, pe.colors.white)
    TEXT_COLOR_CODE = (pe.colors.darkaqua, None)
    TEXT_COLOR_LINK = (pe.colors.darkblue, None)
    DOCUMENT_TITLE_COLOR = ((20, 20, 20), TEXT_COLOR[1])
    DOCUMENT_SUBTITLE_COLOR = ((100, 100, 100), TEXT_COLOR[1])
    TEXT_COLOR_T = (TEXT_COLOR[0], None)
    TEXT_COLOR_H = (TEXT_COLOR[1], None)
    CODE_COLOR = ((120, 120, 120), None)
    LINE_GRAY = (88, 88, 88)
    DOCUMENT_GRAY = (184, 184, 184)
    TRANSPARENT_COLOR = (0, 0, 0, 0)
    BUTTON_ACTIVE_COLOR = (0, 0, 0, 25)
    BUTTON_DISABLED_COLOR = (0, 0, 0, 100)
    BUTTON_DISABLED_LIGHT_COLOR = (255, 255, 255, 150)

    # Colors
    RED = (255, 50, 50)

    # Key bindings
    NAVIGATION_KEYS = {
        "next": [pe.K_RIGHT],
        "previous": [pe.K_LEFT],
    }

    APP_ICON = os.path.join(ICON_DIR, 'moss.png')
    ICO_APP_ICON = os.path.join(ICON_DIR, 'moss.ico')

    IMPORT_TYPES = ['.rm', '.pdf', '.epub']

    PROGRESS_ORDER = [
        "total",
    ]
    PROGRESS_COLOR = {
        "total": pe.colors.white,  # This should never get used!!!
    }


if pe.settings.config.debug:
    print("\nDefaults:")
    for key, value in Defaults.__dict__.items():
        if not key.startswith("__"):
            print(f"{key}: {value}")
    print("^ Defaults ^\n")

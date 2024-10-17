import os.path
import sys
import __main__

try:
    from cefpython3 import cefpython as cef
except ImportError:
    cef = None
import pygameextra as pe

CEF_BASE_SETTINGS = {
    "windowless_rendering_enabled": True,
    'context_menu': {
        "enabled": True,
        "navigation": True,
        "view_source": True,
        "external_browser": False,
        "inspect_element_at": True,
        "print": True,
        "devtools": True
    }
}

CEF_SWITCHES = {
    # GPU acceleration is not supported in OSR mode, so must disable
    # it using these Chromium switches (Issue #240 and #463)
    "disable-gpu": "",
    "disable-gpu-compositing": "",
    "disable-threaded-scrolling": "",
    # Tweaking OSR performance by setting the same Chromium flags
    # as in upstream cefclient (Issue #240).
    "enable-begin-frame-scheduling": "",
    "disable-surfaces": "",  # This is required for PDF ext to work
}

def get_asset_path():
    # Check if we are running in a PyInstaller bundle
    if hasattr(sys, '_MEIPASS'):
        os.chdir(sys._MEIPASS)
        resources_dir = os.path.join(sys._MEIPASS, 'cefpython3')
        settings = {
            **CEF_BASE_SETTINGS,
            'locales_dir_path': os.path.join(resources_dir, 'locales'),
            'resources_dir_path': resources_dir,
            'browser_subprocess_path': os.path.join(resources_dir, 'subprocess.exe'),
            'log_file': os.path.join(resources_dir, 'debug.log')
        }
        asset_dir = os.path.join(sys._MEIPASS, 'assets')
        script_dir = os.path.abspath(os.path.dirname(sys.executable))
    else:
        settings = CEF_BASE_SETTINGS
        asset_dir = os.path.join(os.path.abspath("."), 'assets')
        script_dir = os.path.abspath(os.path.dirname(__main__.__file__))
    # if cef:
    #     cef.Initialize(settings=settings, switches=CEF_SWITCHES)
    return asset_dir, script_dir


class Defaults:
    ASSET_DIR, SCRIPT_DIR = get_asset_path()

    HTML_DIR = os.path.join(ASSET_DIR, 'html')
    ICON_DIR = os.path.join(ASSET_DIR, 'icons')
    FONT_DIR = os.path.join(ASSET_DIR, 'fonts')

    TOKEN_FILE_PATH = os.path.join(SCRIPT_DIR, 'token')
    SYNC_FILE_PATH = os.path.join(SCRIPT_DIR, 'sync')

    CUSTOM_FONT = os.path.join(FONT_DIR, 'Imperator.ttf')
    CUSTOM_FONT_BOLD = os.path.join(FONT_DIR, 'Imperator Bold.ttf')
    MONO_FONT = os.path.join(FONT_DIR, 'JetBrainsMono-Bold.ttf')
    FOLDER_FONT = os.path.join(FONT_DIR, 'Roboto-Medium.ttf')
    PATH_FONT = os.path.join(FONT_DIR, 'Roboto-Regular.ttf')
    DOCUMENT_TITLE_FONT = os.path.join(FONT_DIR, 'Roboto-Regular.ttf')
    DOCUMENT_ERROR_FONT = os.path.join(FONT_DIR, 'Roboto-Medium.ttf')

    LOGO_FONT = CUSTOM_FONT_BOLD
    MAIN_MENU_FONT = CUSTOM_FONT_BOLD
    CODE_FONT = MONO_FONT

    TEXT_COLOR = (pe.colors.black, pe.colors.white)
    DOCUMENT_TITLE_COLOR = ((20, 20, 20), pe.colors.white)
    DOCUMENT_SUBTITLE_COLOR = ((100, 100, 100), pe.colors.white)
    TEXT_COLOR_T = (TEXT_COLOR[0], None)
    CODE_COLOR = ((120, 120, 120), None)
    LINE_GRAY = (88, 88, 88)
    DOCUMENT_GRAY = (184, 184, 184)
    TRANSPARENT_COLOR = (0, 0, 0, 0)
    BUTTON_ACTIVE_COLOR = (0, 0, 0, 25)

    # Colors
    RED = (255, 50, 50)

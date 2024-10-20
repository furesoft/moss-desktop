import appdirs
from .gui import GUI, APP_NAME, AUTHOR
from .__main__ import run_gui

INSTALL_DIR = appdirs.site_data_dir(APP_NAME, AUTHOR)
USER_DATA_DIR = appdirs.user_data_dir(APP_NAME, AUTHOR)

__all__ = ['GUI', 'run_gui', 'INSTALL_DIR', 'USER_DATA_DIR', 'APP_NAME', 'AUTHOR']

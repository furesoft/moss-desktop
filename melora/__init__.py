import os.path

import gui

gui.APP_NAME = "Moss & Melora"


def melora_patch():
    from gui.screens.loader import Loader
    from gui.defaults import Defaults
    Loader.TO_LOAD = {
        **Loader.TO_LOAD
    }
    orig = Defaults.SCRIPT_DIR
    new = os.path.join(Defaults.SCRIPT_DIR, 'melora-extensions')

    os.makedirs(new, exist_ok=True)

    for key, value in Defaults.__dict__.items():
        if isinstance(value, str):
            setattr(Defaults, key, value.replace(orig, new))

    Defaults.MELORA_CONFIG_DIR = os.path.join(new, 'configs')
    os.makedirs(Defaults.MELORA_CONFIG_DIR, exist_ok=True)

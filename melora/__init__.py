import gui

gui.APP_NAME = "Moss & Melora"


def melora_patch():
    from gui.screens.loader import Loader
    Loader.TO_LOAD = {
        **Loader.TO_LOAD
    }

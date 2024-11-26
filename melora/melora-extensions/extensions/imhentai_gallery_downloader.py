import json
import os.path

from gui.defaults import Defaults
from melora.extension_base import ExtensionBase


class Extension(ExtensionBase):
    ID = 'imhentai_gallery_downloader'
    NAME = "ImHentai Gallery Downloader"
    SHORT = 'ImHentai'
    ACTIONS = {
        "Download Gallery": "download_gallery"
    }

    def __init__(self, injector):
        super().__init__(injector)
        self.path_to_config = os.path.join(Defaults.MELORA_CONFIG_DIR, '', 'imhentai_gallery_downloader.json')
        self.config = {}

    def load(self):
        if os.path.exists(self.path_to_config):
            with open(self.path_to_config, 'r') as f:
                self.config = json.load(f)
        else:
            self.save()

    def save(self):
        with open(self.path_to_config, 'w') as f:
            json.dump(self.config, f)

    def download_gallery(self):
        print("this works")

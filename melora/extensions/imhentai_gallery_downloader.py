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

    def download_gallery(self):
        print("this works")

import re
import threading
from io import BytesIO
from traceback import print_exc
from typing import Dict

import pygameextra as pe
from gui.viewer.renderers.shared_model import AbstractRenderer
from rm_lines import rm_bytes_to_svg


# noinspection PyPep8Naming
class Notebook_rM_Lines_Renderer(AbstractRenderer):
    """
    This is a fast renderer for rM lines in SVG format
    Using the RMC project with a few modifications for better inking

    This renderer is also used for debug rendering and previews
    """

    pages: Dict[str, pe.Image]
    RENDER_ERROR = 'Error rendering writing for this page'

    def __init__(self, document_renderer):
        super().__init__(document_renderer)
        self.pages = {}

    def _load(self, page_uuid: str):
        if content := self.document.content_data.get(file_uuid := f'{self.document.uuid}/{page_uuid}.rm'):
            self.pages[file_uuid] = self.generate_image_from_rm(content)
            if self.pages[file_uuid] is not None:
                self.pages[file_uuid].resize(self.size)
        self.document_renderer.loading -= 1

    def load(self):
        self.check_and_load_page(self.document.content.c_pages.last_opened.value)
        self.document_renderer.loading -= 1  # check_and_load_page adds an extra loading

    def handle_event(self, event):
        pass

    def render(self, page_uuid: str):
        page = self.document.content.c_pages.get_page_from_uuid(page_uuid)
        rm_file = f'{self.document.uuid}/{page.id}.rm'

        if rm_file in self.pages:
            if self.pages[rm_file] is None:
                self.error = self.RENDER_ERROR
            else:
                self.pages[rm_file].display((0, 0))
                if self.error and self.error.text == self.RENDER_ERROR:
                    self.error = None
        elif self.error and self.error.text == self.RENDER_ERROR:
            self.error = None
        elif rm_file in self.document.content_files:
            self.check_and_load_page(page_uuid)

    def check_and_load_page(self, page_uuid: str):
        self.document_renderer.loading += 1
        threading.Thread(target=self._load, args=(page_uuid,), daemon=True).start()

    @staticmethod
    def generate_image_from_rm(content: bytes):
        try:
            svg: str = rm_bytes_to_svg(content)
            image = pe.Image(BytesIO(svg.encode("utf-8")))
        except Exception as e:
            print_exc()
            return None
        else:
            return image

    def close(self):
        pass

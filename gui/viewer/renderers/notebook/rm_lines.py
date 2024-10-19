import re
import threading
from io import BytesIO
from typing import Dict

import pygameextra as pe
from gui.viewer.renderers.shared_model import AbstractRenderer
from rm_lines import rm_bytes_to_svg


class NotebookRenderer(AbstractRenderer):
    pages: Dict[str, pe.Image]
    RENDER_ERROR = 'Error rendering writing for this page'

    def __init__(self, document_renderer):
        super().__init__(document_renderer)
        self.pages = {}

    def _load(self):
        for file_uuid, content in self.document.content_data.items():
            if not file_uuid.endswith('.rm'):
                continue
            self.pages[file_uuid] = self.generate_image_from_rm(content)
            if self.pages[file_uuid] is not None:
                self.pages[file_uuid].resize(self.size)
        self.document_renderer.loading -= 1

    def load(self):
        threading.Thread(target=self._load, daemon=True).start()

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

    @staticmethod
    def generate_image_from_rm(content: bytes):
        try:
            svg: str = rm_bytes_to_svg(content)
            image = pe.Image(BytesIO(svg.encode("utf-8")))
        except Exception as e:
            return None
        else:
            return image


    def close(self):
        pass
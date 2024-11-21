import base64
from functools import lru_cache
import os
import threading
import time
import pygameextra as pe

# noinspection PyBroadException
try:
    import fitz
except Exception:
    fitz = None

from gui.defaults import Defaults
from ..shared_model import AbstractRenderer


# noinspection PyPep8Naming
class PDF_PyMuPDF_Viewer(AbstractRenderer):
    def __init__(self, document_renderer):
        super().__init__(document_renderer)
        self.current_page = self.document_renderer.current_page_index

    @property
    @lru_cache
    def pdf_raw(self):
        try:
            return self.document.content_data[f'{self.document.uuid}.pdf']
        except KeyError:
            self.error = 'PDF file missing'
            return None

    def load(self):
        if not self.pdf_raw:
            return

        self.pdf = fitz.open(stream=self.pdf_raw, filetype='pdf')
        self.document_renderer.loading -= 1

    def render(self, page_uuid: str):
        if not self.pdf:
            return
        page_index = self.document_renderer.current_page_index
        image = self.get_page(page_index)

        pe.display.blit(image, (0, 0))

    @lru_cache()
    def get_page(self, page):
        # noinspection PyUnresolvedReferences
        pix = self.pdf[page].get_pixmap()
        mode = "RGBA" if pix.alpha else "RGB"
        # noinspection PyTypeChecker
        image = pe.Surface(surface=pe.pygame.image.frombuffer(pix.samples, (pix.width, pix.height), mode))
        return image

    def close(self):
        pass

    def handle_event(self, event):
        pass

    # def next(self):
    #     if self.pdf:
    #         self.pdf.browser.ExecuteJavascript('window.nextPage()')
    #
    # def previous(self):
    #     if self.pdf:
    #         self.pdf.browser.ExecuteJavascript('window.previousPage()')

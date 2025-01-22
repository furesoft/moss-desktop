from functools import lru_cache

import pygameextra as pe

from rm_api.defaults import RM_SCREEN_SIZE

# noinspection PyBroadException
try:
    import pymupdf
except Exception:
    pymupdf = None

from ..shared_model import AbstractRenderer

# DPI / typographic measurement unit
PDF_SCALING = 227.54 / 72


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
            self.pdf = None
        else:
            self.pdf = pymupdf.open(stream=self.pdf_raw, filetype='pdf')
        self.document_renderer.loading -= 1

    def render(self, page_uuid: str):
        if not self.pdf:
            return
        page = self.document.content.c_pages.get_page_from_uuid(page_uuid)
        if not page.redirect:
            return

        page_index = page.redirect.value
        sprite = self.get_page(page_index)
        base_scale = self.document_renderer.zoom * self.gui.ratios.rm_scaled(RM_SCREEN_SIZE[0])
        scale = base_scale * PDF_SCALING
        sprite.scale = (scale, scale)

        rect = pe.Rect(0, 0, *sprite.size)
        rect.center = self.document_renderer.center
        rect.top = rect.centery - (RM_SCREEN_SIZE[1] // 2) * base_scale
        sprite.display(rect.topleft)

    @lru_cache()
    def get_page(self, page) -> pe.Sprite:
        pdf_page = self.pdf[page]

        # noinspection PyUnresolvedReferences
        pix = pdf_page.get_pixmap()
        mode = "RGBA" if pix.alpha else "RGB"
        # noinspection PyTypeChecker
        sprite = pe.Sprite(sprite_reference=pe.pygame.image.frombuffer(pix.samples, (pix.width, pix.height), mode))
        return sprite

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

from functools import lru_cache

import pygameextra as pe

from rm_api.defaults import RM_SCREEN_SIZE
from . import PDF_AbstractRenderer

# noinspection PyBroadException
try:
    import pymupdf
except Exception:
    pymupdf = None

# DPI / typographic measurement unit
PDF_SCALING = 227.54 / 72


# noinspection PyPep8Naming
class PDF_PyMuPDF_Viewer(PDF_AbstractRenderer):

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
        pdf_zoom_enhance = self.get_enhance_scale()
        sprite = self.get_page(page_index, pdf_zoom_enhance)

        # Calculate the scale and remarkable scale of the page
        base_scale = self.document_renderer.zoom * self.gui.ratios.rm_scaled(RM_SCREEN_SIZE[0])

        # Scale the PDF to the screen
        scale = (base_scale * PDF_SCALING) / pdf_zoom_enhance

        # Set the scale of the sprite
        sprite.scale = (scale, scale)

        rect = pe.Rect(0, 0, *sprite.size)
        rect.center = self.document_renderer.center
        # Align the PDF to the top
        rect.top = rect.centery - (RM_SCREEN_SIZE[1] // 2) * base_scale
        sprite.display(rect.topleft)

    @lru_cache()
    def get_page(self, page, scale=1) -> pe.Sprite:
        pdf_page = self.pdf[page]

        # Scale up the PDF if required
        matrix = pymupdf.Matrix(scale, scale)

        # noinspection PyUnresolvedReferences
        pix = pdf_page.get_pixmap(matrix=matrix)
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

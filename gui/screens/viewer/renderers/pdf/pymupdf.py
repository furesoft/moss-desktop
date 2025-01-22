from functools import lru_cache

import pygameextra as pe

from rm_api.defaults import RM_SCREEN_SIZE
from . import PDF_AbstractRenderer
from ..shared_model import LoadTask

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
        task = self.task_get_page(page_index, pdf_zoom_enhance)

        if not (task.loaded and self.document_renderer.zoom_ready):
            pdf_zoom_enhance = 1
            sprite = self.get_page(page_index, 1)
        else:
            sprite = task.sprite

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

        screen_rect = pe.Rect(0, 0, *self.size)

        # Clip the visible area of the PDF
        clipped_area = screen_rect.clip(rect)

        # Remove the rect position from the clip
        clipped_area.move_ip(-rect.left, -rect.top)
        # Move the rect by the clipped area offset
        rect.move_ip(clipped_area.left, clipped_area.top)

        # Finally render the PDF
        sprite.display(rect.topleft, clipped_area)

    @lru_cache()
    def get_page(self, page, scale: float = 1) -> pe.Sprite:
        pdf_page = self.pdf[page]

        # Scale up the PDF if required
        matrix = pymupdf.Matrix(scale, scale)

        # noinspection PyUnresolvedReferences
        pix = pdf_page.get_pixmap(matrix=matrix)
        mode = "RGBA" if pix.alpha else "RGB"
        # noinspection PyTypeChecker
        sprite = pe.Sprite(sprite_reference=pe.pygame.image.frombuffer(pix.samples, (pix.width, pix.height), mode))
        return sprite

    @lru_cache()
    def task_get_page(self, page, scale: float = 1) -> LoadTask:
        return LoadTask(self.get_page, page, scale)

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

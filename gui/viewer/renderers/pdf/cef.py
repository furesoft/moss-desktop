import base64
from functools import lru_cache
import os
import threading
import time
import pygameextra as pe

# noinspection PyBroadException
try:
    from CEF4pygame import CEFpygame
except Exception:
    CEFpygame = None

from gui.defaults import Defaults
from ..shared_model import AbstractRenderer


# noinspection PyPep8Naming
class PDF_CEF_Viewer(AbstractRenderer):
    PDF_HTML = os.path.join(Defaults.HTML_DIR, 'pdf.html')

    def __init__(self, document_renderer):
        super().__init__(document_renderer)
        self.pdf: CEFpygame = None
        self.injected_js = False
        self.js_code = None
        self.url_should_be = None
        self.current_page = self.document_renderer.current_page_index

    @property
    @lru_cache
    def pdf_raw(self):
        try:
            for file in self.document.files:
                if file.uuid == f'{self.document.uuid}.pdf':
                    return self.document.content_data[file.uuid]
        except IndexError:
            self.error = 'PDF file missing'
            return None

    def load(self):
        if not self.pdf_raw:
            return
        url = f'{os.path.abspath(self.PDF_HTML)}'
        try:
            self.pdf = CEFpygame(
                URL=url,
                VIEWPORT_SIZE=self.size
            )
        except AssertionError:
            self.error = 'CEF not available, try restarting the application'
            return

        # Convert the PDF data to base64
        base64_pdf = base64.b64encode(self.pdf_raw).decode('utf-8').replace('\n', '')

        # Send the PDF data to JavaScript
        self.js_code = f"""
            (function checkLoadPdf() {{
                if (typeof window.loadPdf === 'function') {{
                    window.loadPdf("{base64_pdf}", {self.width}, {self.height}, {self.current_page});
                }} else {{
                    setTimeout(checkLoadPdf, 100);
                }}
            }})();
        """

    def handle_event(self, event):
        browser = None
        if self.pdf:
            browser = self.pdf
        if not browser:
            return

        if event.type == pe.pygame.QUIT:
            run = 0
        if event.type == pe.pygame.MOUSEMOTION:
            browser.motion_at(*event.pos)

        # Prevent right-click context menu
        if event.type == pe.pygame.MOUSEBUTTONDOWN and (self.gui.config.debug or event.button == 1):
            browser.mousedown_at(*event.pos, event.button)
        if event.type == pe.pygame.MOUSEBUTTONUP and (self.gui.config.debug or event.button == 1):
            browser.mouseup_at(*event.pos, event.button)

    def render(self, page_uuid: str):
        if not self.pdf:
            return
        if self.url_should_be:
            if self.pdf.browser.GetUrl() != self.url_should_be:
                self.close()
                self.document_renderer.load()
                return
            if not self.injected_js:
                self.pdf.browser.ExecuteJavascript(self.js_code)
                self.injected_js = True

            page = self.document.content.c_pages.get_page_from_uuid(page_uuid)
            if not page.redirect:
                return

            page_index = page.redirect.value

            if self.current_page != page_index:
                self.current_page = page_index
                self.pdf.browser.ExecuteJavascript(f'window.loadPage({self.current_page})')

            pe.display.blit(self.pdf.image)
        elif (url := self.pdf.browser.GetUrl()) and self.pdf.image.get_at((0, 0))[2] != 51:
            self.url_should_be = url
        else:
            _ = self.pdf.image

    def close(self):
        if self.pdf:
            self.pdf.exit_app()


    # def next(self):
    #     if self.pdf:
    #         self.pdf.browser.ExecuteJavascript('window.nextPage()')
    #
    # def previous(self):
    #     if self.pdf:
    #         self.pdf.browser.ExecuteJavascript('window.previousPage()')

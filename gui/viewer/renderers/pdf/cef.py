import base64
from functools import lru_cache
import os
import threading
import time
import pygameextra as pe
from CEF4pygame import CEFpygame

from gui.defaults import Defaults
from ..shared_model import AbstractRenderer


class PDF_CEF_Viewer(AbstractRenderer):
    PDF_HTML = os.path.join(Defaults.HTML_DIR, 'pdf.html')

    def __init__(self, document_renderer):
        super().__init__(document_renderer)
        self.pdf = None
        self.injected_js = False
        self.js_code = None
    
    @property
    @lru_cache
    def pdf_raw(self):
        try:
            return self.document.content_data[self.document.content_files[0]]
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
                    window.loadPdf("{base64_pdf}", {self.width}, {self.height});
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
        if event.type == pe.pygame.MOUSEBUTTONDOWN:
            browser.mousedown_at(*event.pos, event.button)
        if event.type == pe.pygame.MOUSEBUTTONUP:
            browser.mouseup_at(*event.pos, event.button)
        if event.type == pe.pygame.KEYDOWN:
            browser.keydown(event.key)
        if event.type == pe.pygame.KEYUP:
            browser.keyup(event.key)

    def render(self):
        if not self.pdf:
            return
        if self.pdf.image.get_at((0, 0))[2] != 51:
            if not self.injected_js:
                self.pdf.browser.ExecuteJavascript(self.js_code)
                self.injected_js = True
            pe.display.blit(self.pdf.image)

    def close(self):
        if self.pdf:
            self.pdf.browser.CloseBrowser()

    def next(self):
        if self.pdf:
            self.pdf.browser.ExecuteJavascript('window.nextPage()')

    def previous(self):
        if self.pdf:
            self.pdf.browser.ExecuteJavascript('window.previousPage()')

    @property
    def page(self):
        return 1
    
    @property
    def page_count(self):
        return 10
import base64
import io
import os
import threading
import time
from logging import lastResort

import pygameextra as pe
from typing import TYPE_CHECKING, Dict
try:
    import CEF4pygame

    CEF4pygame.print = lambda *args, **kwargs: None
    from CEF4pygame import CEFpygame
    from cefpython3 import cefpython as cef
except Exception:
    CEFpygame = None
    cef = None

from PIL import Image

from .defaults import Defaults
from .pp_helpers import DraggablePuller

if TYPE_CHECKING:
    from .gui import GUI
    from queue import Queue
    from rm_api.models import Document
    from .gui import ConfigType


class DocumentRenderer(pe.ChildContext):
    LAYER = pe.BEFORE_POST_LAYER
    DOT_TIME = .4

    config: 'ConfigType'

    def __init__(self, parent: 'GUI', document: 'Document'):
        self.document = document
        self.loading = True
        self.pdf: CEFpygame = None
        self._error = None

        self.loading_rect = pe.Rect(
            0, 0,
            parent.ratios.document_viewer_loading_square,
            parent.ratios.document_viewer_loading_square
        )
        self.loading_rect.center = parent.center
        split = self.loading_rect.width // 3
        self.first_dot = self.loading_rect.x + split * 0.5
        self.second_dot = self.loading_rect.x + split * 1.5
        self.third_dot = self.loading_rect.x + split * 2.5
        self.loading_timer = time.time()
        self.mode = 'nocontent'

        super().__init__(parent)

        self.load()

    @property
    def error(self):
        return self._error

    @error.setter
    def error(self, value):
        self._error = pe.Text(
            value,
            Defaults.DOCUMENT_ERROR_FONT,
            self.ratios.document_viewer_error_font_size,
            pe.Rect(0, 0, *self.size).center,
            Defaults.TEXT_COLOR
        )
        self.loading = False

    def load_pdf_with_cef(self, pdf_raw: bytes):
        pdf_html = os.path.join(Defaults.HTML_DIR, 'pdf.html')
        url = f'{os.path.abspath(pdf_html)}'
        self.pdf = CEFpygame(
            URL=url,
            VIEWPORT_SIZE=self.size
        )
        # Convert the PDF data to base64
        base64_pdf = base64.b64encode(pdf_raw).decode('utf-8').replace('\n', '')

        # Send the PDF data to JavaScript
        js_code = f"""
            (function checkLoadPdf() {{
                if (typeof window.loadPdf === 'function') {{
                    window.loadPdf("{base64_pdf}", {self.width}, {self.height});
                }} else {{
                    setTimeout(checkLoadPdf, 100);
                }}
            }})();
        """

        self.pdf.__setattr__('inject_js', js_code)
        self.pdf.__setattr__('injected_js', False)

    def handle_events_with_cef(self, event):
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

    def handle_event(self, event):
        if self.pdf and self.mode.endswith('cef'):
            self.handle_events_with_cef(event)

    def load(self):
        if self.document.content['fileType'] == 'pdf':
            try:
                pdf_raw = self.document.content_data[self.document.content_files[0]]
            except IndexError:
                self.error = 'PDF file missing'
                return
            if self.config.pdf_render_mode == 'cef' and CEFpygame:
                self.load_pdf_with_cef(pdf_raw)
            elif self.config.pdf_render_mode == 'none':
                self.error = 'Could not render PDF'
            else:
                self.error = 'Could not render PDF. Make sure you have a compatible PDF renderer'
        else:
            self.error = 'Unknown format. Could not render document'
        self.loading = False

    def pre_loop(self):
        # Draw the loading icon
        if self.loading:
            pe.draw.rect(pe.colors.black, self.loading_rect)
            section = (time.time() - self.loading_timer) / self.DOT_TIME
            if section > 0.5:
                pe.draw.circle(pe.colors.white, (self.first_dot, self.loading_rect.centery),
                               self.ratios.document_viewer_loading_circle_radius)
            if section > 2:
                pe.draw.circle(pe.colors.white, (self.second_dot, self.loading_rect.centery),
                               self.ratios.document_viewer_loading_circle_radius)
            if section > 3:
                pe.draw.circle(pe.colors.white, (self.third_dot, self.loading_rect.centery),
                               self.ratios.document_viewer_loading_circle_radius)
            if section > 3.5:
                self.loading_timer = time.time()

    def render_pdf_with_cef(self):
        if self.pdf.image.get_at((0, 0))[2] != 51:
            if not self.pdf.injected_js:
                self.pdf.browser.ExecuteJavascript(self.pdf.inject_js)
                self.pdf.injected_js = True
            pe.display.blit(self.pdf.image)

    def loop(self):
        if self.loading:
            return
        if self.pdf and self.mode.endswith('cef'):
            self.render_pdf_with_cef()

    def close(self):
        if self.pdf and self.mode.endswith('cef'):
            self.pdf.browser.CloseBrowser()

    def post_loop(self):
        if self.error:
            self.error.display()


class DocumentViewer(pe.ChildContext):
    LAYER = pe.AFTER_LOOP_LAYER

    screens: 'Queue'
    icons: Dict[str, pe.Image]

    def __init__(self, parent: 'GUI', document_uuid: str):
        top_rect = pe.Rect(
            0, 0,
            parent.width,
            parent.ratios.document_viewer_top_draggable_height
        )
        self.document = parent.api.documents[document_uuid]
        self.top_puller = DraggablePuller(
            parent, top_rect,
            detect_y=-top_rect.height, callback_y=self.close,
            draw_callback_y=self.draw_close_indicator
        )
        self.document_renderer = DocumentRenderer(parent, self.document)
        super().__init__(parent)

    def loop(self):
        self.document_renderer()
        self.top_puller()

    def handle_event(self, event):
        self.document_renderer.handle_event(event)

    def close(self):
        self.document_renderer.close()
        del self.screens.queue[-1]

    def draw_close_indicator(self):
        # Handles the closing indicator when pulling down
        icon = self.icons['chevron_down']
        icon_rect = pe.Rect(0, 0, *icon.size)
        top = self.top_puller.rect.centery
        bottom = min(self.height // 4, pe.mouse.pos()[1])  # Limit the bottom to 1/4 of the screen

        # Calculate the center of the icon
        icon_rect.centerx = self.top_puller.rect.centerx
        icon_rect.centery = top + (bottom - top) * .5
        # Lerp to half of the length between the top and the bottom points

        # Make a rect between the top puller and the bottom icon rect
        outline_rect = pe.Rect(0, 0, icon_rect.width, icon_rect.bottom - self.top_puller.rect.centery)
        outline_rect.midbottom = icon_rect.midbottom

        # Inflate the rect to make it an outline
        outline_rect.inflate_ip(self.ratios.pixel(5), self.ratios.pixel(5))

        # Draw the outline, the line and the arrow icon
        pe.draw.rect(pe.colors.white, outline_rect)
        pe.draw.line(Defaults.LINE_GRAY, (x_pos := self.top_puller.rect.centerx-self.ratios.pixel(2), self.top_puller.rect.centery), (x_pos, icon_rect.centery), self.ratios.pixel(3))
        icon.display(icon_rect.topleft)

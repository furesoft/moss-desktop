import base64
import io
import os
import threading
import time
from logging import lastResort

import pygameextra as pe
from typing import TYPE_CHECKING, Dict

from gui.viewer.renderers.pdf.cef import PDF_CEF_Viewer

try:
    import CEF4pygame

    CEF4pygame.print = lambda *args, **kwargs: None
    from CEF4pygame import CEFpygame
    from cefpython3 import cefpython as cef
except Exception:
    CEFpygame = None
    cef = None

from PIL import Image

from ..defaults import Defaults
from ..pp_helpers import DraggablePuller

if TYPE_CHECKING:
    from ..gui import GUI, ConfigType
    from queue import Queue
    from rm_api.models import Document


class DocumentRenderer(pe.ChildContext):
    LAYER = pe.BEFORE_POST_LAYER
    DOT_TIME = .4

    config: 'ConfigType'

    PAGE_NAVIGATION_DELAY = 0.2  # Initial button press delay
    PAGE_NAVIGATION_SPEED = 0.1  # After initial button press delay

    def __init__(self, parent: 'GUI', document: 'Document'):
        self.document = document
        self.loading = True
        self.began_loading = False
        self._error = None
        self.hold_next = False
        self.hold_previous = False
        self.hold_timer = 0

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
        self.renderer = None
        super().__init__(parent)

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

    def handle_navigation(self, event):
        if not self.hold_timer:
            if any([
                pe.event.key_DOWN(key)
                for key in Defaults.NAVIGATION_KEYS['next']
            ]):
                self.hold_next = True
                self.hold_timer = time.time() + self.PAGE_NAVIGATION_DELAY
                self.do_next()
            if any([
                pe.event.key_DOWN(key)
                for key in Defaults.NAVIGATION_KEYS['previous']
            ]):
                self.hold_previous = True
                self.hold_timer = time.time() + self.PAGE_NAVIGATION_DELAY
                self.do_previous()
        else:
            if any([
                pe.event.key_UP(key)
                for key in Defaults.NAVIGATION_KEYS['next'] + Defaults.NAVIGATION_KEYS['previous']
            ]):
                self.hold_next = False
                self.hold_previous = False
                self.hold_timer = None

    @property
    def can_do_next(self):
        return self.renderer.page < self.renderer.page_count

    @property
    def can_do_previous(self):
        return self.renderer.page > 0

    def do_next(self):
        if self.can_do_next:
            self.renderer.next()

    def do_previous(self):
        if self.can_do_previous:
            self.renderer.previous()

    def handle_event(self, event):
        if self.loading or not self.renderer:
            return
        self.renderer.handle_event(event)
        self.handle_navigation(event)

    def load(self):
        if self.document.content.file_type == 'pdf':
            if self.config.pdf_render_mode == 'cef' and CEFpygame:
                self.renderer = PDF_CEF_Viewer(self)
            elif self.config.pdf_render_mode == 'none':
                self.error = 'Could not render PDF'
            else:
                self.error = 'Could not render PDF. Make sure you have a compatible PDF renderer'
        else:
            self.error = 'Unknown format. Could not render document'
        if self.renderer:
            self.renderer.load()
        self.loading = False

    def pre_loop(self):
        if not self.began_loading:
            self.load()
            self.began_loading = True
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

    def loop(self):
        if self.loading or not self.renderer:
            return
        self.renderer.render()

    def close(self):
        if self.renderer:
            self.renderer.close()

    def post_loop(self):
        if self.error:
            self.error.display()
        if self.hold_timer and time.time() > self.hold_timer:
            if self.hold_next:
                self.do_next()
            elif self.hold_previous:
                self.do_previous()
            self.hold_timer = time.time() + self.PAGE_NAVIGATION_SPEED



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
        pe.draw.line(Defaults.LINE_GRAY,
                     (x_pos := self.top_puller.rect.centerx - self.ratios.pixel(2), self.top_puller.rect.centery),
                     (x_pos, icon_rect.centery), self.ratios.pixel(3))
        icon.display(icon_rect.topleft)

"""
PP stands for Post Processing
This script contains small child contexts to render on top of everything else
"""
import io
import os
import shutil
import time
from functools import lru_cache
from typing import TYPE_CHECKING

import pygameextra as pe
import rmscene

from gui.defaults import Defaults
from rm_api.storage.v3 import get_file_contents

if TYPE_CHECKING:
    from gui.aspect_ratio import Ratios
    from gui import GUI


class FullTextPopup(pe.ChildContext):
    LAYER = pe.AFTER_LOOP_LAYER
    EXISTING = {}

    def __init__(self, parent: 'GUI', text: pe.Text, referral_text: pe.Text = None):
        self.text = text

        # Set the position of the text
        if referral_text is not None:
            self.text.rect.center = referral_text.rect.center
        else:
            self.text.rect.midbottom = pe.mouse.pos()

        # Make sure the text is inside the screen
        screen_rect = pe.Rect(0, 0, *parent.size)
        screen_rect.scale_by_ip(.98, .98)
        self.text.rect.clamp_ip(screen_rect)

        self.used_at = time.time()
        super().__init__(parent)

    def pre_loop(self):
        outline_rect = self.text.rect.inflate(self.ratios.pixel(10), self.ratios.pixel(10))
        pe.draw.rect(pe.colors.white, outline_rect, 0)
        pe.draw.rect(pe.colors.black, outline_rect, self.ratios.pixel(2))

    def loop(self):
        self.text.display()

    def post_loop(self):
        self.used_at = time.time()

    @classmethod
    def create(cls, parent: 'GUI', text: pe.Text, referral_text: pe.Text = None):
        if cls.EXISTING.get(id(text)) is None:
            cls.EXISTING[id(text)] = cls(parent, text, referral_text)
            return cls.EXISTING[id(text)]
        if time.time() - cls.EXISTING[id(text)].used_at < .05:
            return cls.EXISTING[id(text)]
        else:
            del cls.EXISTING[id(text)]
            return cls.create(parent, text, referral_text)


class DocumentDebugPopup(pe.ChildContext):
    LAYER = pe.AFTER_LOOP_LAYER
    EXISTING = {}

    ratios: 'Ratios'
    TEXTS = [
        "Extract files",
        "Close"
    ]

    def __init__(self, parent: 'GUI', document: 'Document', position):
        self.document = document
        self.position = position
        self.used_at = time.time()
        self.popup_rect = pe.Rect(*position, parent.ratios.main_menu_document_width, parent.ratios.main_menu_document_height)
        self.popup_rect.clamp_ip(pe.Rect(0, 0, *parent.size))
        self.button_actions = {
            'extract': self.extract_files,
            'close': self.close
        }
        self.texts = [
            pe.Text(
                text,
                Defaults.DEBUG_FONT, parent.ratios.debug_text_size,
                colors=Defaults.TEXT_COLOR_H
            )
            for text in self.TEXTS
        ]
        super().__init__(parent)

    def pre_loop(self):
        pe.draw.rect((0, 0, 0, 100), self.popup_rect, 0)

    def loop(self):
        x = self.popup_rect.left
        y = self.popup_rect.top
        h = self.popup_rect.height // len(self.button_actions)
        for (item, action), text in zip(
            self.button_actions.items(),
            self.texts
        ):
            pe.button.rect(
                (x, y, self.popup_rect.width, h),
                Defaults.TRANSPARENT_COLOR, Defaults.BUTTON_ACTIVE_COLOR,
                action=action,
                text=text
            )
            y += h


    def post_loop(self):
        pe.draw.rect(pe.colors.brown, self.popup_rect, self.ratios.pixel(3))
        self.used_at = time.time()

    @classmethod
    def create(cls, parent: 'GUI', document: 'Document', position):
        key = id(document)
        if cls.EXISTING.get(key) is None:
            cls.EXISTING.clear()
            cls.EXISTING[key] = cls(parent, document, position)
            return cls.EXISTING[key]
        if time.time() - cls.EXISTING[key].used_at < .05:
            return cls.EXISTING[key]
        else:
            cls.EXISTING.clear()
            return cls.create(parent, document, position)

    def close(self):
        self.EXISTING.clear()

    @property
    @lru_cache
    def extract_location(self):
        return os.path.join(os.path.dirname(Defaults.SYNC_FILE_PATH), 'sync_exports', str(self.document.parent), self.document.uuid+'_extract')

    def clean_extract_location(self):
        if os.path.isdir(self.extract_location):
            shutil.rmtree(self.extract_location, ignore_errors=True)
        os.makedirs(self.extract_location, exist_ok=True)
        with open(os.path.join(self.extract_location, f'$ {self.document.metadata.visible_name}'), 'w') as f:
            f.write('')

    def clean_file_uuid(self, file):
        return file.uuid.replace(f'{self.document.uuid}/', '')

    def extract_files(self):
        self.clean_extract_location()

        for file in self.document.files:
            # Fetch the file
            data: bytes = get_file_contents(self.api, file.hash, binary=True, use_cache=False)
            file_path = os.path.join(self.extract_location, self.clean_file_uuid(file))

            # Save the file
            with open(file_path, 'wb') as f:
                f.write(data)



class DraggablePuller(pe.ChildContext):
    LAYER = pe.BEFORE_POST_LAYER

    def __init__(
            self,
            parent: 'GUI', rect,
            detect_x: int = None, detect_y: int = None,
            callback_x=None, callback_y=None,
            draw_callback_x=None, draw_callback_y=None
    ):
        self.rect = rect
        self.draggable = pe.Draggable(self.rect.topleft, self.rect.size)
        self.detect_x = detect_x
        self.detect_y = detect_y
        self.callback_x = callback_x
        self.callback_y = callback_y
        self.draw_callback_x = draw_callback_x
        self.draw_callback_y = draw_callback_y
        super().__init__(parent)

    def loop(self):
        dragging, pos = self.draggable.check()

        # Uncomment the following line to see the draggable area
        # pe.draw.rect(pe.colors.red, (*pos, *self.draggable.area), 1)

        move_amount = tuple(original - current for original, current in zip(self.rect.topleft, pos))
        if move_amount[0] == 0 and move_amount[1] == 0:
            return
        if self.detect_x is not None and self.callback_x is not None:
            if 0 < self.detect_x < move_amount[0]:
                if not dragging:
                    self.callback_x()
                elif self.draw_callback_x is not None:
                    self.draw_callback_x()
            elif 0 > self.detect_x > move_amount[0]:
                if not dragging:
                    self.callback_x()
                elif self.draw_callback_x is not None:
                    self.draw_callback_x()
        if self.detect_y is not None and self.callback_y is not None:
            if 0 < self.detect_y < move_amount[1]:
                if not dragging:
                    self.callback_y()
                elif self.draw_callback_y is not None:
                    self.draw_callback_y()
            elif 0 > self.detect_y > move_amount[1]:
                if not dragging:
                    self.callback_y()
                elif self.draw_callback_y is not None:
                    self.draw_callback_y()

        if not dragging:
            self.draggable.pos = self.rect.topleft

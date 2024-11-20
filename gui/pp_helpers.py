"""
PP stands for Post Processing
This script contains small child contexts to render on top of everything else
"""
import io
import os
import shutil
import time
import json
from functools import lru_cache
from traceback import print_exc
from typing import TYPE_CHECKING

import pygameextra as pe
from colorama import Fore

from gui.defaults import Defaults
import rm_api.models as models
from rm_api.storage.v3 import get_file_contents, get_file, make_files_request
from rm_lines import rm_bytes_to_svg


if TYPE_CHECKING:
    from rm_api.models import Document
    from gui.aspect_ratio import Ratios
    from gui import GUI


class FullTextPopup(pe.ChildContext):
    LAYER = pe.AFTER_LOOP_LAYER
    EXISTING = {}

    def __init__(self, parent: 'GUI', text: pe.Text, referral_text: pe.Text = None, offset = None):
        self.text = text
        self.offset = offset

        # Set the position of the text
        if referral_text is not None:
            self.text.rect.center = referral_text.rect.center
        else:
            self.text.rect.midbottom = pe.mouse.pos()

        # Make sure the text is inside the screen
        screen_rect = pe.Rect(0, 0, *parent.size)
        screen_rect.scale_by_ip(.98, .98)
        self.text.rect.x += offset[0]
        self.text.rect.y += offset[1]
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
    def create(cls, parent: 'GUI', text: pe.Text, referral_text: pe.Text = None, offset = None):
        if cls.EXISTING.get(id(text)) is None:
            cls.EXISTING[id(text)] = cls(parent, text, referral_text, offset)
            return cls.EXISTING[id(text)]
        if time.time() - cls.EXISTING[id(text)].used_at < .05:
            return cls.EXISTING[id(text)]
        else:
            del cls.EXISTING[id(text)]
            return cls.create(parent, text, referral_text, offset)


class DocumentDebugPopup(pe.ChildContext):
    LAYER = pe.AFTER_LOOP_LAYER
    EXISTING = {}

    ratios: 'Ratios'

    def __init__(self, parent: 'GUI', document: 'Document', position):
        self.document = document
        self.position = position
        self.used_at = time.time()
        self.popup_rect = pe.Rect(*position, parent.ratios.main_menu_document_width,
                                  parent.ratios.main_menu_document_height)
        self.popup_rect.clamp_ip(pe.Rect(0, 0, *parent.size))
        self.button_actions = {
            'Extract files': self.extract_files,
            'Render pages': self.render_pages,
            'Render important': lambda: self.render_pages(True),
            'Close': self.close
        }
        self.texts = {
            text: pe.Text(
                text,
                Defaults.DEBUG_FONT, parent.ratios.debug_text_size,
                colors=Defaults.TEXT_COLOR_H
            )
            for text in self.button_actions.keys()
        }
        super().__init__(parent)

    def pre_loop(self):
        pe.draw.rect((0, 0, 0, 100), self.popup_rect, 0)

    def loop(self):
        x = self.popup_rect.left
        y = self.popup_rect.top
        h = self.popup_rect.height // len(self.button_actions)
        for item, action in self.button_actions.items():
            pe.button.rect(
                (x, y, self.popup_rect.width, h),
                Defaults.TRANSPARENT_COLOR, Defaults.BUTTON_ACTIVE_COLOR,
                action=action,
                text=self.texts[item]
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
        return os.path.join(os.path.dirname(Defaults.SYNC_FILE_PATH), 'sync_exports', str(self.document.parent),
                            self.document.uuid)

    @property
    @lru_cache
    def important_extract_location(self):
        return os.path.join(os.path.dirname(Defaults.SYNC_FILE_PATH), 'sync_exports', 'important')

    def clean_extract_location(self, location=None):
        location = location or self.extract_location
        if os.path.isdir(location):
            shutil.rmtree(location, ignore_errors=True)
        os.makedirs(location, exist_ok=True)
        with open(os.path.join(location, f'$ {self.clean_filename(self.document.metadata.visible_name)}'),
                  'w') as f:
            _, lines = get_file(self.api, self.api.get_root()['hash'], use_cache=False, raw=True)
            for line in lines:
                file = models.File.from_line(line)
                if file.uuid == self.document.uuid:
                    f.write(line)
                    f.write(
                        make_files_request(self.api, "GET", file.hash, use_cache=False, binary=True).decode()
                    )

    def clean_file_uuid(self, file):
        return file.uuid.replace(f'{self.document.uuid}/', '')

    @staticmethod
    def clean_filename(filename):
        return "".join(c for c in filename if c.isalpha() or c.isdigit() or c == ' ').rstrip()

    def extract_files(self):
        self.clean_extract_location()

        for file in self.document.files:
            # Fetch the file
            try:
                data: bytes = get_file_contents(self.api, file.hash, binary=True, use_cache=False)
            except:
                print(f"{Fore.RED}Could not fetch file with UUID={file.uuid} HASH={file.hash}{Fore.RESET}")
                continue
            file_path = os.path.join(self.extract_location, self.clean_file_uuid(file))

            is_json = file.uuid.rsplit('.')[-1] in ("content", "metadata")

            if self.config.add_ext_to_raw_exports and is_json:
                file_path += '.json'

            # Save the file
            with open(file_path, 'wb') as f:
                if self.config.format_raw_exports and is_json:
                    data = json.dumps(json.loads(data), indent=4, sort_keys=True).encode()
                f.write(data)

    def render_pages(self, important: bool = False):
        if important:
            location = self.important_extract_location
        else:
            location = self.extract_location
        self.clean_extract_location(location)
        i = 0
        files = [file for file in self.document.files if file.uuid.endswith('.rm')]
        try:
            files.sort(key=lambda file: self.document.content.c_pages.get_index_from_uuid(file.uuid.split('/')[-1].split('.')[0]))
        except Exception as e:
            print_exc()
            pass

        for file in files:
            data: bytes = get_file_contents(self.api, file.hash, binary=True, use_cache=False)
            file_path = os.path.join(location, f'{i:>03} {self.clean_file_uuid(file)}.svg')

            # Render and save
            try:
                svg: str = rm_bytes_to_svg(data)
                with open(file_path, 'w') as f:
                    f.write(svg)
            except Exception as e:
                print_exc()
            i += 1


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

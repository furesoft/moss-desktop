import os
import shutil
import threading

import pygameextra as pe
from typing import TYPE_CHECKING, Dict

from gui import APP_NAME, INSTALL_DIR
from gui.defaults import Defaults

if TYPE_CHECKING:
    from gui import GUI
    from rm_api import API


class Installer(pe.ChildContext):
    LAYER = pe.AFTER_LOOP_LAYER
    icons: Dict[str, pe.Image]
    api: 'API'

    def __init__(self, parent: 'GUI'):
        self.installing = False
        super().__init__(parent)
        self.logo = pe.Text(
            APP_NAME,
            Defaults.LOGO_FONT, self.ratios.loader_logo_text_size,
            pe.math.center(
                (
                    0, 0, self.width,
                    self.height - (
                            self.ratios.loader_loading_bar_height + self.ratios.loader_loading_bar_padding
                    )
                )
            ),
            Defaults.TEXT_COLOR
        )
        self.cancel_text = pe.Text(
            "Cancel",
            Defaults.INSTALLER_FONT, self.ratios.installer_buttons_size,
            colors=Defaults.TEXT_COLOR_T
        )
        self.install_text = pe.Text(
            "Install",
            Defaults.INSTALLER_FONT, self.ratios.installer_buttons_size,
            colors=Defaults.TEXT_COLOR_T
        )
        self.line_rect = pe.Rect(0, 0, self.ratios.loader_loading_bar_width,
                                 self.ratios.loader_loading_bar_height)
        self.line_rect.midtop = self.logo.rect.midbottom
        self.line_rect.top += self.ratios.loader_loading_bar_padding
        buttons_rect = pe.Rect(0, 0, self.ratios.installer_buttons_width, self.ratios.installer_buttons_height)
        buttons_rect.midtop = self.line_rect.midtop
        self.cancel_button_rect = buttons_rect.scale_by(.5, 1)
        self.cancel_button_rect.width -= self.ratios.installer_buttons_padding // 2
        self.cancel_button_rect.left = buttons_rect.left
        self.install_button_rect = self.cancel_button_rect.copy()
        self.install_button_rect.right = buttons_rect.right
        self.total = 0
        self.progress = 0
        
    def draw_button_outline(self, rect):
        pe.draw.rect(Defaults.LINE_GRAY, rect, self.ratios.pixel(3))

    def loop(self):
        self.logo.display()
        if self.installing:
            pe.draw.rect(pe.colors.black, self.line_rect, 1)
            progress_rect = self.line_rect.copy()
            progress_rect.width *= self.progress / self.total
            pe.draw.rect(pe.colors.black, progress_rect, 0)
        else:
            pe.button.rect(
                self.cancel_button_rect,
                Defaults.TRANSPARENT_COLOR, Defaults.BUTTON_ACTIVE_COLOR,
                action=self.cancel,
                text=self.cancel_text
            )
            pe.button.rect(
                self.install_button_rect,
                Defaults.TRANSPARENT_COLOR, Defaults.BUTTON_ACTIVE_COLOR,
                action=self.install,
                text=self.install_text
            )
            self.draw_button_outline(self.cancel_button_rect)
            self.draw_button_outline(self.install_button_rect)

    def cancel(self):
        del self.screens.queue[-1]

    def install_thread(self):
        self.installing = True
        for root, dirs, files in os.walk(self.from_directory):
            rel_path = os.path.relpath(root, self.from_directory)
            dest_path = os.path.join(self.to_directory, rel_path)
            os.makedirs(dest_path, exist_ok=True)

            for file in files:
                src_file = os.path.join(root, file)
                dst_file = os.path.join(dest_path, file)

                print(f"COPY FROM: {src_file}\nTO: {dst_file}\n")

                shutil.copy2(src_file, dst_file)
                self.progress += 1
        

    def install(self):
        self.total = sum([len(files) for _, _, files in os.walk(self.from_directory)])
        threading.Thread(target=self.install_thread, daemon=False).start()

    @property
    def from_directory(self):
        return Defaults.SCRIPT_DIR

    @property
    def to_directory(self):
        return INSTALL_DIR

import re
import threading
from functools import lru_cache
from io import BytesIO
from traceback import print_exc
from typing import Dict, Tuple, Union

import pygameextra as pe

from gui.screens.viewer.renderers.notebook.expanded_notebook import ExpandedNotebook
from gui.screens.viewer.renderers.shared_model import AbstractRenderer
from rm_api.models import Metadata
from rm_lines import rm_bytes_to_svg
from rm_lines.inker.document_size_tracker import NotebookSizeTracker, PDFSizeTracker


class rM_Lines_ExpandedNotebook(ExpandedNotebook):
    WIDTH_PATTERN = r'width="([\d.]+)"'
    HEIGHT_PATTERN = r'height="([\d.]+)"'
    VIEWPORT_PATTERN = r'viewBox="([\d.-]+) ([\d.-]+) ([\d.]+) ([\d.]+)"'

    def __init__(self, svg: str, track_xy: NotebookSizeTracker,
                 use_lock: threading.Lock = None):
        super().__init__(track_xy)
        self.svg = svg
        self.width_match = re.search(self.WIDTH_PATTERN, self.svg)
        self.height_match = re.search(self.HEIGHT_PATTERN, self.svg)
        self.viewbox_match = re.search(self.VIEWPORT_PATTERN, self.svg)
        self.use_lock = use_lock

    @lru_cache()
    def get_frame_from_initial(self, frame_x, frame_y, final_width: int = None, final_height: int = None) -> pe.Image:
        # Replace the svg viewport with a viewport to capture the frame

        width = float(self.width_match.group(1))
        height = float(self.height_match.group(1))
        x = float(self.viewbox_match.group(1))
        y = float(self.viewbox_match.group(2))
        w = float(self.viewbox_match.group(3))
        h = float(self.viewbox_match.group(4))

        if final_width is None:
            final_width = int(width)
        if final_height is None:
            final_height = int(height)

        # Replace values in the SVG content
        svg_content = re.sub(self.WIDTH_PATTERN, f'width="{final_width}"', self.svg)
        svg_content = re.sub(self.HEIGHT_PATTERN, f'height="{final_height}"', svg_content)
        svg_content = re.sub(self.VIEWPORT_PATTERN,
                             f'viewBox="'
                             f'{frame_x * self.frame_width - self.track_xy.offset_x} '
                             f'{frame_y * self.frame_height - self.track_xy.offset_y} '
                             f'{self.frame_width} '
                             f'{self.frame_height}"',
                             svg_content)

        encoded_svg_content = svg_content.encode()
        # if self.use_lock:
        #     with self.use_lock:
        #         return pe.Image(BytesIO(encoded_svg_content), (final_width, final_height))
        # else:
        return pe.Image(BytesIO(encoded_svg_content), (final_width, final_height))


# noinspection PyPep8Naming
class Notebook_rM_Lines_Renderer(AbstractRenderer):
    """
    This is a fast renderer for rM lines in SVG format
    Using the RMC project with a few modifications for better inking

    This renderer is also used for debug rendering and previews
    """

    pages: Dict[str, Union[rM_Lines_ExpandedNotebook, None]]
    RENDER_ERROR = 'Error rendering writing for this page'

    def __init__(self, document_renderer):
        super().__init__(document_renderer)
        self.pages = {}

    def _load(self, page_uuid: str):
        if content := self.document.content_data.get(file_uuid := f'{self.document.uuid}/{page_uuid}.rm'):
            self.pages[file_uuid] = self.generate_expanded_notebook_from_rm(self.document.metadata, content,
                                                                            size=self.size)
        self.document_renderer.loading -= 1

    def load(self):
        self.check_and_load_page(self.document.content.c_pages.last_opened.value)
        self.document_renderer.loading -= 1  # check_and_load_page adds an extra loading

    def handle_event(self, event):
        pass

    def render(self, page_uuid: str):
        page = self.document.content.c_pages.get_page_from_uuid(page_uuid)
        rm_file = f'{self.document.uuid}/{page.id}.rm'

        if rm_file in self.pages:
            if self.pages[rm_file] is None:
                self.error = self.RENDER_ERROR
            else:
                # TODO: replace with get frames and use offsets and aknowledge each frame offset when displaying
                self.pages[rm_file].get_frame_from_initial(0, 0, *self.size).display()
                if self.error and self.error.text == self.RENDER_ERROR:
                    self.error = None
        elif self.error and self.error.text == self.RENDER_ERROR:
            self.error = None
        elif rm_file in self.document.content_files:
            self.check_and_load_page(page_uuid)

    def check_and_load_page(self, page_uuid: str):
        self.document_renderer.loading += 1
        threading.Thread(target=self._load, args=(page_uuid,), daemon=True).start()

    @staticmethod
    def generate_expanded_notebook_from_rm(metadata: Metadata, content: bytes, size: Tuple[int, int] = None,
                                           use_lock: threading.Lock = None) -> rM_Lines_ExpandedNotebook:
        try:
            if metadata.type == 'DocumentType':
                track_xy = NotebookSizeTracker()
            else:
                track_xy = PDFSizeTracker()
            svg: str = rm_bytes_to_svg(content, track_xy)
            expanded = rM_Lines_ExpandedNotebook(svg, track_xy, use_lock)
            expanded.get_frame_from_initial(0, 0, *(size if size else ()))
        except Exception as e:
            print_exc()
            return None
        else:
            return expanded

    def close(self):
        pass

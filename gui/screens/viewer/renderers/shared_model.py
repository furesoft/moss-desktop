import threading
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rm_api.models import Document
    from gui import GUI
    from gui.screens.viewer.viewer import DocumentRenderer


class AbstractRenderer(ABC):
    def __init__(self, document_renderer: 'DocumentRenderer'):
        self.document_renderer = document_renderer
        self.gui: 'GUI' = document_renderer.parent_context
        self.document: 'Document' = document_renderer.document

    @property
    def error(self):
        return self.document_renderer.error

    @error.setter
    def error(self, value):
        self.document_renderer.error = value

    @property
    def size(self):
        return self.document_renderer.size

    @property
    def width(self):
        return self.document_renderer.width

    @property
    def height(self):
        return self.document_renderer.height

    @abstractmethod
    def load(self):
        ...

    @abstractmethod
    def handle_event(self, event):
        ...

    @abstractmethod
    def render(self, page_uuid: str):
        ...

    @abstractmethod
    def close(self):
        ...

    def get_enhance_scale(self):
        # Return an enhancement scale for when the page is zoomed in
        # Will at most return between 1 and 4.5
        scale = max(2, min(9, self.document_renderer.zoom // 0.5)) * 0.5
        return scale / self.document_renderer.config.scale


class LoadTask:
    def __init__(self, function, *args, **kwargs):
        self.loaded = False
        self.sprite = None
        self.function = function
        self.args = args
        self.kwargs = kwargs
        threading.Thread(target=self.load, daemon=True).start()

    def load(self):
        self.sprite = self.function(*self.args, **self.kwargs)
        self.loaded = True

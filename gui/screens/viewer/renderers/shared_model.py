from typing import TYPE_CHECKING
from abc import ABC, abstractmethod

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

from gui.preview_handler import PreviewHandler
from gui.screens.viewer import DocumentViewer
from rm_api import Document, Content


class ContentWrapper:
    def __init__(self, callback_document: 'CallbackDocument', content: Content):
        self.callback = callback_document
        self.content = content

    def __getattr__(self, item):
        if item == 'callback':
            return self.callback
        if item == 'usable':
            self.callback.callback()
            return False
        if self.callback.uuid in DocumentViewer.PROBLEMATIC_DOCUMENTS:
            DocumentViewer.PROBLEMATIC_DOCUMENTS.remove(self.callback.uuid)
        if self.callback.maintain_preview and self.callback.uuid not in PreviewHandler.CACHED_PREVIEW:
            PreviewHandler.CACHED_PREVIEW[self.callback.uuid] = self.callback.maintain_preview
        return getattr(self.content, item)


class CallbackDocument(Document):
    def __init__(self, *args, callback=None, **kwargs):
        self._content = None
        self.maintain_preview = None
        self.callback = callback
        super().__init__(*args, **kwargs)

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, value):
        self._content = ContentWrapper(self, value)

from rm_api import Document, Content


class ContentWrapper:
    def __init__(self, callback, content: Content):
        self.callback = callback
        self.content = content

    def __getattr__(self, item):
        if item == 'callback':
            return self.callback
        if item == 'usable':
            self.callback()
            return False
        return getattr(self.content, item)


class CallbackDocument(Document):
    def __init__(self, *args, callback = None, **kwargs):
        self._content = None
        super().__init__(*args, **kwargs)
        self.callback = callback

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, value):
        self._content = ContentWrapper(self.callback, value)

    def post_patch(self, callback):
        self.callback = callback
        if isinstance(self._content, ContentWrapper):
            self._content.callback = callback
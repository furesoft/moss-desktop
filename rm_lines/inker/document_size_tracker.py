from abc import ABC

# The screen size of the Remarkable 2
SCREEN_WIDTH = 1404
SCREEN_HEIGHT = 1872


class DocumentSizeTracker(ABC):
    def __init__(self, document_center_x, document_center_y, document_cap_top, document_cap_bottom, document_cap_left,
                 document_cap_right, frame_width, frame_height, offset_x, offset_y):
        self.document_center_x = document_center_x
        self.document_center_y = document_center_y
        self.document_cap_top = document_cap_top
        self.document_cap_bottom = document_cap_bottom
        self.document_cap_left = document_cap_left
        self.document_cap_right = document_cap_right
        self._track_top = 0
        self.track_bottom = frame_height
        self._track_left = 0
        self.track_right = frame_width
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.offset_x = offset_x
        self.offset_y = offset_y

    @property
    def track_top(self):
        return self._track_top

    @property
    def track_left(self):
        return self._track_left

    @property
    def track_width(self):
        return self.track_right - self.track_left

    @property
    def track_height(self):
        return self.track_bottom - self.track_top

    @track_top.setter
    def track_top(self, value):
        diff = value - self._track_top
        self._track_top = value
        self.track_bottom += diff

    @track_left.setter
    def track_left(self, value):
        diff = value - self._track_left
        self._track_left = value
        self.track_right += diff * 2

    def x(self, x):
        aligned_x = x + SCREEN_WIDTH / 2
        if aligned_x > self.track_right:
            self.track_right = aligned_x
        if aligned_x < self.track_left:
            self.track_left = aligned_x

        return x

    def y(self, y):
        if y > self.track_bottom:
            self.track_bottom = y
        if y < self.track_top:
            self.track_top = y
        return y

    @property
    def format_kwargs(self):
        return {
            'height': self.track_height,
            'width': self.track_width,
            'x_shift': SCREEN_WIDTH / 2,
            'viewbox': f'{self.track_left} {self.track_top} {self.track_width} {self.track_height}',
        }


class NotebookSizeTracker(DocumentSizeTracker):
    def __init__(self):
        super().__init__(0, 0, 0, 0, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0)


class PDFSizeTracker(DocumentSizeTracker):
    def __init__(self):
        width = SCREEN_WIDTH * 1.4
        height = SCREEN_HEIGHT * 1.4
        offset_x = SCREEN_WIDTH * 0.2
        super().__init__(0, 0, 0, 0, 0, 0, width, height, offset_x, -10)

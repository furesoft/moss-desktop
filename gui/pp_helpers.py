"""
PP stands for Post Processing
This script contains small child contexts to render on top of everything else
"""
import time

import pygameextra as pe


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

from .common import INJECTOR_COLOR
from gui import GUI
import pygameextra as pe


class InjectorMenu(pe.ChildContext):
    LAYER = pe.AFTER_LOOP_LAYER
    parent_context: GUI

    def __init__(self, injector: 'Injector'):
        self.injector = injector
        self.rect = None
        super().__init__(injector.parent_context)

    def pre_loop(self):
        self.rect = pe.Rect(0, 0, self.width // 2, self.height)
        self.rect.right = self.width + self.width * (1 - self.injector.t)
        self.rect.top -= self.height * (1 - self.injector.t)
        pe.button.rect(self.rect, INJECTOR_COLOR, INJECTOR_COLOR, action_set={
            'hover': {
                'action': self.injector.hover_hold
            },
            'hover_draw': None
        }, name='moss_extender')

    def loop(self):
        pass

from functools import lru_cache

import pygameextra as pe
from abc import ABC, abstractmethod
from typing import Tuple, Dict, List
from gui.defaults import Defaults


class ContextBar(pe.ChildContext, ABC):
    LAYER = pe.AFTER_LOOP_LAYER
    BUTTONS: Tuple[dict] = ()

    # definitions from GUI
    icons: Dict[str, pe.Image]
    ratios: 'Ratios'

    # Scaled button texts
    texts: List[pe.Text]

    def __init__(self, parent: 'MainMenu'):
        self.texts = []
        self.main_menu = parent
        super().__init__(parent.parent_context)
        self.handle_scales()

    @property
    @lru_cache()
    def buttons(self) -> List[pe.RectButton]:
        width, height = 0, 0
        buttons: List[pe.RectButton] = []
        for i, button in enumerate(self.BUTTONS):
            icon = self.icons[button['icon']]
            rect = pe.Rect(
                0, 0,
                self.texts[i].rect.width + icon.width * 1.5,
                self.ratios.main_menu_top_height
            )
            rect.inflate_ip(self.ratios.main_menu_x_padding, -self.ratios.main_menu_x_padding)
            disabled = button.get('disabled', False)
            buttons.append((
                pe.RectButton(
                    rect,
                    Defaults.TRANSPARENT_COLOR,
                    Defaults.BUTTON_ACTIVE_COLOR,
                    action_set={
                        'l_click': {
                            'action': getattr(self, button['action']) if button['action'] else None
                        },
                        'r_click': {
                            'action': self.handle_new_context_menu,
                            'args': (getattr(self, context_menu), i)
                        } if (context_menu := button.get('context_menu')) else None,
                        'hover_draw': None,
                        'hover': None
                    },
                    disabled=disabled,
                    name=f'context_bar<{id(self)}>.button_{i}'
                )
            ))
            width += buttons[-1].area.width
            height += buttons[-1].area.height
        self.finalize_button_rect(buttons, width, height)

        return buttons

    def handle_new_context_menu(self, context_menu_getter, index):
        context_menu = context_menu_getter(self.buttons[index].area.bottomleft)
        if not context_menu:
            return
        if context_menu:
            context_menu()
            self.BUTTONS[index]['_context_menu'] = context_menu

    @abstractmethod
    def finalize_button_rect(self, buttons, width, height):
        ...

    @property
    def button_data_zipped(self):
        return zip(self.buttons, self.BUTTONS, self.texts)

    def handle_scales(self):
        # Cache reset
        self.texts.clear()
        self.__class__.buttons.fget.cache_clear()

        # Handle texts so we know their size
        for button_meta in self.BUTTONS:
            self.texts.append(pe.Text(
                button_meta['text'], Defaults.MAIN_MENU_BAR_FONT, self.ratios.main_menu_bar_size,
                colors=Defaults.TEXT_COLOR_T
            ))

        # Process final text and icon positions inside button and padding
        for button, button_meta, button_text in self.button_data_zipped:
            # Position the button text with padding

            button_text.rect.midright = button.area.midright
            button_text.rect.right -= self.ratios.main_menu_button_padding

            # Position the icon with padding
            icon = self.icons[button_meta['icon']]
            icon_rect = pe.Rect(0, 0, *icon.size)

            icon_rect.midleft = button.area.midleft
            icon_rect.left += self.ratios.main_menu_button_padding

            button_meta['icon_rect'] = icon_rect

            # Position the context icon with padding
            context_icon = self.icons['context_menu']
            context_icon_rect = pe.Rect(0, 0, *context_icon.size)

            context_icon_rect.bottomright = button.area.bottomright
            context_icon_rect.left -= self.ratios.main_menu_button_padding / 2
            context_icon_rect.top -= self.ratios.main_menu_button_padding / 2

            button_meta['context_icon_rect'] = context_icon_rect

    def loop(self):
        for button, button_meta, button_text in self.button_data_zipped:
            pe.settings.game_context.buttons.append(button)
            pe.button.check_hover(button)
            button_text.display()

            icon = self.icons[button_meta['icon']]
            icon.display(button_meta['icon_rect'].topleft)

            if button.action_set['r_click']:
                context_icon = self.icons['context_menu']
                context_icon.display(button_meta['context_icon_rect'].topleft)

            if button.disabled:
                pe.draw.rect(Defaults.BUTTON_DISABLED_LIGHT_COLOR, button.area)

            if context_menu := button_meta.get('_context_menu'):
                if context_menu.can_close:
                    button_meta['_context_menu'] = None
                context_menu()

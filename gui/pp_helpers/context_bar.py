from functools import lru_cache

import pygameextra as pe
from abc import ABC, abstractmethod
from typing import Tuple, Dict, List, Optional
from gui.defaults import Defaults


class ContextBar(pe.ChildContext, ABC):
    LAYER = pe.AFTER_LOOP_LAYER
    TEXT_COLOR = Defaults.TEXT_COLOR_T
    TEXT_COLOR_INVERTED = Defaults.TEXT_COLOR_H
    BUTTONS: Tuple[Dict[str, Optional[str]]] = ()
    INVERT = False

    # definitions from GUI
    icons: Dict[str, pe.Image]
    ratios: 'Ratios'

    # Scaled button texts
    texts: List[pe.Text]
    texts_inverted: List[pe.Text]

    def __init__(self, parent: 'MainMenu'):
        self.texts = []
        self.texts_inverted = []
        self.main_menu = parent
        self.initialized = False
        parent.quick_refresh()
        super().__init__(parent.parent_context)

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
                    Defaults.BUTTON_ACTIVE_COLOR if button['action'] else Defaults.TRANSPARENT_COLOR,
                    action_set={
                        'l_click': {
                            'action': getattr(self, button['action']) if button['action'] else lambda: None,
                            'args': button.get('data', ()),
                        },
                        'r_click': {
                            'action': self.handle_new_context_menu,
                            'args': (getattr(self, context_menu), i)
                        } if (context_menu := button.get('context_menu')) else None,
                        'hover_draw': None,
                        'hover': None
                    },
                    disabled=(Defaults.BUTTON_DISABLED_COLOR if self.INVERT else Defaults.BUTTON_DISABLED_LIGHT_COLOR)
                    if disabled else False,
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
        return zip(self.buttons, self.BUTTONS, self.texts, self.texts_inverted)

    def handle_scales(self):
        # Cache reset
        self.texts.clear()
        self.texts_inverted.clear()
        self.__class__.buttons.fget.cache_clear()

        # Handle texts so we know their size
        for button_meta in self.BUTTONS:
            self.texts.append(pe.Text(
                button_meta['text'], Defaults.MAIN_MENU_BAR_FONT, self.ratios.main_menu_bar_size,
                colors=self.TEXT_COLOR
            ))
            self.texts_inverted.append(pe.Text(
                button_meta['text'], Defaults.MAIN_MENU_BAR_FONT, self.ratios.main_menu_bar_size,
                colors=self.TEXT_COLOR_INVERTED
            ))

        # Process final text and icon positions inside button and padding
        for button, button_meta, button_text, button_text_inverted in self.button_data_zipped:
            # Position the icon with padding
            icon = self.icons[button_meta['icon']]
            icon_rect = pe.Rect(0, 0, *icon.size)

            icon_rect.midleft = button.area.midleft
            icon_rect.left += self.button_margin

            # Position the button text with padding
            button_text.rect.midleft = icon_rect.midright
            button_text.rect.left += self.button_padding
            button_text_inverted.rect.center = button_text.rect.center

            button_meta['icon_rect'] = icon_rect

            # Position the context icons with padding
            for icon_key in (
                    'context_menu', 'chevron_right', 'chevron_down', 'small_chevron_right', 'small_chevron_down'):
                context_icon = self.icons[icon_key]
                context_icon_rect = pe.Rect(0, 0, *context_icon.size)

                if 'right' in icon_key:
                    context_icon_rect.midright = button.area.midright
                else:
                    context_icon_rect.bottomright = button.area.bottomright
                    context_icon_rect.top -= self.button_margin / 2
                context_icon_rect.left -= self.button_margin / 2
                button_meta[f'{icon_key}_icon_rect'] = context_icon_rect

    @property
    def button_margin(self):
        return self.ratios.main_menu_button_margin

    @property
    def button_padding(self):
        return self.ratios.main_menu_button_padding

    @property
    def currently_inverted(self):
        return None

    def pre_loop(self):
        if not self.initialized:
            self.handle_scales()
            self.initialized = True

    def loop(self):
        for button, button_meta, button_text, button_text_inverted in self.button_data_zipped:
            if inverted_id := button_meta.get('inverted_id'):
                is_inverted = (self.INVERT or inverted_id == self.currently_inverted)
            else:
                is_inverted = self.INVERT
            if is_inverted:
                pe.draw.rect(Defaults.SELECTED, button.area)
            pe.settings.game_context.buttons.append(button)
            if not button_meta['action']:
                button.active_resource = Defaults.TRANSPARENT_COLOR
            elif is_inverted:
                button.active_resource = Defaults.BUTTON_ACTIVE_COLOR_INVERTED
            else:
                button.active_resource = Defaults.BUTTON_ACTIVE_COLOR
            pe.button.check_hover(button)

            if is_inverted:
                button_text_inverted.display()
            else:
                button_text.display()

            icon = self.icons[button_meta['icon']]
            if is_inverted:
                icon = self.icons.get(f'{button_meta["icon"]}_inverted', icon)
            icon.display(button_meta['icon_rect'].topleft)

            if context_icon_type := button_meta.get('context_icon'):
                if context_icon_type == 'context_menu':
                    context_icon = self.icons['context_menu'] if not is_inverted else self.icons[
                        'context_menu_inverted']
                    context_icon.display(button_meta['context_menu_icon_rect'].topleft)
                elif context_icon_type == 'chevron_right':
                    context_icon = self.icons['chevron_right'] if not is_inverted else self.icons[
                        'chevron_right_inverted']
                    context_icon.display(button_meta['chevron_right_icon_rect'].topleft)
                elif context_icon_type == 'chevron_down':
                    context_icon = self.icons['chevron_down'] if not is_inverted else self.icons[
                        'chevron_down_inverted']
                    context_icon.display(button_meta['chevron_down_icon_rect'].topleft)
                elif context_icon_type == 'small_chevron_right':
                    context_icon = self.icons['small_chevron_right'] if not is_inverted else self.icons[
                        'small_chevron_right_inverted']
                    context_icon.display(button_meta['small_chevron_right_icon_rect'].topleft)
                elif context_icon_type == 'small_chevron_down':
                    context_icon = self.icons['small_chevron_down'] if not is_inverted else self.icons[
                        'small_chevron_down_inverted']
                    context_icon.display(button_meta['small_chevron_down_icon_rect'].topleft)

            if button.disabled:
                pe.draw.rect(Defaults.BUTTON_DISABLED_COLOR if self.INVERT else Defaults.BUTTON_DISABLED_LIGHT_COLOR,
                             button.area)

            if context_menu := button_meta.get('_context_menu'):
                if context_menu.is_closed:
                    button_meta['_context_menu'] = None
                context_menu()

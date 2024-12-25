import pygameextra as pe

from gui.defaults import Defaults
from gui.events import ResizeEvent
from gui.gui import APP_NAME
from gui.rendering import render_button_using_text
from gui.screens.mixins import ButtonReadyMixin, TitledMixin


class Guides(pe.ChildContext, ButtonReadyMixin, TitledMixin):
    LAYER = pe.AFTER_LOOP_LAYER
    BUTTON_TEXTS = {
        'close': 'Close',
        'next': 'Next',
        'prev': 'Previous'
    }

    SECTIONS = {
        'welcome': {
            'title': f'Welcome to {APP_NAME}!',
            'content': f'This is a simple guide to help you get started!\n'
                       'You can use the buttons below to navigate through the different sections.\n\n'
                       'If you need help, feel free to ask for it in our discord.\n'
                       'Scan this QR code to join our discord server!',
            'image': 'discord_qr_code',
            'prev': None,
            'next': 'about'
        },
        'about': {
            'title': f'About!',
            'content': f'{APP_NAME} is a replacement for the reMarkable cloud app.\n'
                       'DISCLAIMER: This app is not affiliated with reMarkable.\n\n'
                       'Notable features:\n'
                       '1. You can download only the documents you need!\n'
                       '2. Light sync:\n'
                       '      You can upload a smaller version of document\n'
                       '      and archive it on your tablet before uploading the full version.\n'
                       f'3. You can use {APP_NAME} completely offline!\n\n'
                       f'{APP_NAME} is open source and can be found on GitHub.\n'
                       'You can request new features or report bugs on our GitHub page.\n'
                       'You can also join our discord server and vote on new features!',

            'image': None,
            'prev': 'welcome',
            'next': 'doc_view'
        },
        'doc_view': {
            'title': f'Main Menu',
            'content': 'You can navigate your documents here.\n'
                       'It has an interface similar to the reMarkable tablet.\n'
                       'At the top, you will find options to create a new notebook,\n'
                       'folder or import new documents.\n\n'
                       'You can left click on any document to view it.\n'
                       'You can also right click on a document to select it.\n\n'
                       'Selection mode:\n'
                       '1. You can select multiple documents by right clicking on them.\n'
                       '2. You will find options on the top bar to manage your selection.\n\n'
                       'Side bar:\n'
                       '1. You can use the side bar to filter your documents.\n'
                       '2. You can go into the settings and trash\n'
                       'You should be familiar with this menu as you used it to get here!',

            'image': None,
            'prev': 'about',
            'next': None
        },
    }

    def __init__(self, parent):
        super().__init__(parent)
        self.description = pe.Text('', Defaults.GUIDES_FONT, self.ratios.popup_description_size,
                                   colors=Defaults.TEXT_COLOR_T)
        self.change_to_section(self.config.last_guide)
        self.handle_texts()
        self.api.add_hook('guides_resize_check', self.resize_check_hook)

    def resize_check_hook(self, event):
        if isinstance(event, ResizeEvent):
            self.handle_texts()

    @property
    def section(self):
        return self.config.last_guide

    @section.setter
    def section(self, value):
        self.config.last_guide = value
        self.parent_context.dirty_config = True

    def change_to_section(self, section: str):
        self.section = section
        self.handle_title(self.SECTIONS[section]['title'])
        self.description.text = self.SECTIONS[section]['content']
        self.description.init()
        self.description.rect.top = self.title.rect.bottom + self.ratios.popup_description_padding
        self.description.rect.left = self.title.rect.left

    def prev(self):
        self.change_to_section(self.SECTIONS[self.section]['prev'])

    def next(self):
        self.change_to_section(self.SECTIONS[self.section]['next'])

    def close(self):
        del self.screens.queue[-1]

    def loop(self):
        self.title.display()
        self.description.display()

        if image := self.SECTIONS[self.section].get('image'):
            self.icons[image].display(
                (self.title.rect.left, self.description.rect.bottom + self.ratios.popup_description_padding))

        render_button_using_text(self.parent_context, self.texts['prev'], outline=self.ratios.outline,
                                 action=self.prev, name='guides.prev_button',
                                 disabled=False if self.SECTIONS[self.section]['prev'] else (0, 0, 0, 50))

        render_button_using_text(self.parent_context, self.texts['next'], outline=self.ratios.outline,
                                 action=self.next, name='guides.next_button',
                                 disabled=False if self.SECTIONS[self.section]['next'] else (0, 0, 0, 50))

        render_button_using_text(self.parent_context, self.texts['close'], outline=self.ratios.outline,
                                 action=self.close, name='guides.close_button')

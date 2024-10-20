from functools import lru_cache
from typing import TYPE_CHECKING, Dict
import pygameextra as pe

from gui.defaults import Defaults
from gui.pp_helpers import FullTextPopup, DocumentDebugPopup
from gui.preview_handler import PreviewHandler
from gui.screens.viewer import DocumentViewer

if TYPE_CHECKING:
    from gui import GUI
    from rm_api.models import DocumentCollection
    from rm_api.models import Document
    from queue import Queue


def render_full_collection_title(gui: 'GUI', texts, collection_uuid: str, rect):
    pe.draw.rect(Defaults.LINE_GRAY, rect, gui.ratios.pixel(3))
    text = texts[collection_uuid]
    text_full = texts[collection_uuid + '_full']
    if text.text != text_full.text:
        FullTextPopup.create(gui, text_full, text)()


def render_collection(gui: 'GUI', collection: 'DocumentCollection', texts: pe.Text, callback, x, y):
    icon = gui.icons['folder_inverted']
    icon.display((x, y))
    text = texts[collection.uuid]
    text.rect.midleft = (x, y)
    text.rect.x += icon.width + gui.ratios.main_menu_folder_padding
    text.rect.y += icon.height // 1.5
    text.display()
    rect = pe.rect.Rect(
        x, y,
        gui.ratios.main_menu_document_width -
        gui.ratios.main_menu_folder_padding,
        icon.height
    )
    rect.inflate_ip(gui.ratios.main_menu_folder_margin_x, gui.ratios.main_menu_folder_margin_y)
    render_button_using_text(
        gui, text,
        Defaults.TRANSPARENT_COLOR, Defaults.TRANSPARENT_COLOR,
        name=collection.uuid + '_title_hover',
        hover_draw_action=render_full_collection_title,
        hover_draw_data=(gui, texts, collection.uuid, rect),
        action=callback, data=collection.uuid,
        rect=rect
    )
    # pe.button.rect(
    #     rect,
    #     Defaults.TRANSPARENT_COLOR, Defaults.TRANSPARENT_COLOR,
    #     action=callback, data=collection.uuid,
    #     hover_draw_action=pe.draw.rect,
    #     hover_draw_data=(Defaults.LINE_GRAY, rect, gui.ratios.pixel(3))
    # )


def render_full_document_title(gui: 'GUI', texts, document_uuid: str):
    text = texts[document_uuid]
    text_full = texts[document_uuid + '_full']
    if text.text != text_full.text:
        FullTextPopup.create(gui, text_full, text)()


def open_document(gui: 'GUI', document_uuid: str):
    gui.screens.put(DocumentViewer(gui, document_uuid))


def open_document_debug_menu(gui: 'GUI', document: 'Document', position):
    DocumentDebugPopup.create(gui, document, position)()


def render_document(gui: 'GUI', rect: pe.Rect, texts, document: 'Document'):
    # Check if the document is being debugged and keep the debug menu open

    title_text = texts[document.uuid]

    title_text.rect.topleft = rect.bottomleft
    title_text.rect.top += gui.ratios.main_menu_document_title_height_margin

    action = document.ensure_download_and_callback
    data = lambda: open_document(gui, document.uuid)
    disabled = document.downloading

    render_button_using_text(
        gui, title_text,
        Defaults.TRANSPARENT_COLOR, Defaults.TRANSPARENT_COLOR,
        name=document.uuid + '_title_hover',
        hover_draw_action=render_full_document_title,
        hover_draw_data=(gui, texts, document.uuid),
        action=action,
        data=data,
        disabled=disabled
    )

    # Render the notebook icon
    preview = PreviewHandler.get_preview(document, rect.size)
    if not preview:
        notebook_large = gui.icons['notebook_large']
        notebook_large_rect = pe.Rect(0, 0, *notebook_large.size)
        notebook_large_rect.center = rect.center
        notebook_large.display(notebook_large_rect.topleft)
    else:
        preview.display(rect.topleft)

    # Render the availability cloud icon
    if not document.available:
        if document.downloading:
            cloud_icon: pe.Image = gui.icons['cloud_download']
        else:
            cloud_icon: pe.Image = gui.icons['cloud']
        cloud_icon_rect = pe.Rect(0, 0, *cloud_icon.size)

        # Add padding
        cloud_icon_padded_rect = cloud_icon_rect.inflate(gui.ratios.main_menu_document_cloud_padding,
                                                         gui.ratios.main_menu_document_cloud_padding)

        cloud_icon_padded_rect.scale_by_ip(1, .75)  # The icon itself is square, but the padded box is not
        cloud_icon_padded_rect.bottomright = rect.bottomright

        cloud_icon_rect.center = cloud_icon_padded_rect.center

        pe.draw.rect(pe.colors.white, cloud_icon_padded_rect)  # Give the cloud icon a white background with padding
        cloud_icon.display(cloud_icon_rect.topleft)

    # Render the passive outline
    pe.draw.rect(
        Defaults.DOCUMENT_GRAY,
        rect, gui.ratios.pixel(2)
    )
    # Render the button
    pe.button.rect(
        rect,
        Defaults.TRANSPARENT_COLOR, Defaults.BUTTON_ACTIVE_COLOR,
        name=document.uuid,
        action=action,
        data=data,
        disabled=disabled
    )
    if gui.config.debug and (popup := DocumentDebugPopup.EXISTING.get(id(document))) is not None:
        open_document_debug_menu(gui, document, rect.topleft)
    elif gui.config.debug:
        debug_text = pe.Text(
            'DEBUG',
            Defaults.DEBUG_FONT,
            gui.ratios.small_debug_text_size,
            colors=Defaults.TEXT_COLOR_H
        )
        # Inflate a rect around the debug text
        inflated_rect = debug_text.rect.inflate(gui.ratios.pixel(20), gui.ratios.pixel(20))
        inflated_rect.topright = rect.topright
        debug_text.rect.center = inflated_rect.center

        def draw_debug_background():
            # Draw the original_background
            pe.draw.rect(Defaults.BUTTON_ACTIVE_COLOR, rect)
            # Draw a background for the debug button
            pe.draw.rect(pe.colors.darkgray, inflated_rect)

        pe.button.action(
            inflated_rect,
            hover_draw_action=draw_debug_background,
            name=document.uuid + '_debug',
            action=open_document_debug_menu,
            data=(gui, document, rect.topleft)
        )

        debug_text.display()


def render_button_using_text(
        gui: 'GUI', text: pe.Text,
        inactive_color=Defaults.TRANSPARENT_COLOR, active_color=Defaults.BUTTON_ACTIVE_COLOR,
        *args,
        name: str = None, action=None, data=None,
        rect: pe.Rect = None,
        **kwargs
):
    text.display()
    pe.button.rect(
        rect or gui.ratios.pad_button_rect(text.rect),
        inactive_color, active_color,
        *args,
        name=name,
        action=action,
        data=data,
        **kwargs
    )


def render_header(gui: 'GUI', texts: Dict[str, pe.Text], callback, path_queue: 'Queue'):
    render_button_using_text(gui, texts['my_files'], action=callback)

    x = texts['my_files'].rect.right + gui.ratios.main_menu_path_padding
    y = texts['my_files'].rect.centery

    width = 0
    skips = 0

    # Calculate the width of the path
    for item in path_queue.queue:
        text_key = f'path_{item}'
        width += gui.icons['chevron_right'].width + texts[text_key].rect.width

    # Calculate the number of items to skip in the path, this results in the > > you see in the beginning
    while width > gui.width - (x + 200):
        skips += 1
        width -= texts[f'path_{path_queue.queue[-skips]}'].rect.width

    # Draw the path
    for i, item in enumerate(reversed(path_queue.queue)):
        text_key = f'path_{item}'

        # Draw the arrow
        if i >= skips or i < 1:  # Making sure to render the arrow only for the first skip, making sure to avoid > > > >
            gui.icons['chevron_right'].display((x, y - gui.icons['chevron_right'].height // 2))

            x += gui.icons['chevron_right'].width
            if i == 0:
                x += gui.ratios.main_menu_path_first_padding

        # Draw the text only if it's not skipped
        if i >= skips:
            texts[text_key].rect.midleft = (x, y)
            render_button_using_text(gui, texts[text_key], action=callback, data=item)
            x += texts[text_key].rect.width


@lru_cache
def get_bottom_bar_rect(gui: 'GUI'):
    return pe.Rect(0, gui.height - gui.ratios.bottom_bar_height, gui.width, gui.ratios.bottom_bar_height)


def draw_bottom_bar(gui: 'GUI'):
    # The entire lower bar
    pe.draw.rect(
        pe.colors.black,
        get_bottom_bar_rect(gui)
    )


def draw_bottom_loading_bar(gui: 'GUI', current: int, total: int):
    draw_bottom_bar(gui)
    bottom_bar_rect = get_bottom_bar_rect(gui)
    loading_bar_rect = pe.Rect(0, 0, gui.ratios.bottom_loading_bar_width, gui.ratios.bottom_loading_bar_height)
    loading_bar_rect.midright = bottom_bar_rect.midright
    loading_bar_rect.x -= gui.ratios.bottom_loading_bar_padding

    # Draw the loading bar background
    pe.draw.rect(Defaults.LINE_GRAY, loading_bar_rect, 0)

    loading_bar_rect.width = int(loading_bar_rect.width * current / total)

    pe.draw.rect(pe.colors.white, loading_bar_rect, 0)

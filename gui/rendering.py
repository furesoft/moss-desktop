from functools import lru_cache
from typing import TYPE_CHECKING, Dict, Tuple, Union
import pygameextra as pe

from gui.defaults import Defaults
from gui.pp_helpers import FullTextPopup, DocumentDebugPopup
from gui.preview_handler import PreviewHandler
from gui.screens.viewer import DocumentViewer
from gui.screens.viewer.viewer import CannotRenderDocument
from rm_api import DocumentSyncProgress

if TYPE_CHECKING:
    from gui import GUI
    from rm_api.models import DocumentCollection
    from rm_api.models import Document
    from queue import Queue


def render_full_collection_title(gui: 'GUI', texts, collection_uuid: str, rect):
    pe.draw.rect(Defaults.OUTLINE_COLOR, rect, gui.ratios.outline)
    text = texts[collection_uuid]
    text_full = texts[collection_uuid + '_full']
    if text.text != text_full.text:
        FullTextPopup.create(gui, text_full, text)()


def render_full_text(gui: 'GUI', text: pe.Text):
    FullTextPopup.create(gui, text, text)()


def render_collection(gui: 'GUI', collection: 'DocumentCollection', texts: Dict[str, pe.Text], callback, x, y, width):
    icon = gui.icons['folder_inverted'] if collection.has_items else gui.icons['folder']
    icon.display((x, y))
    try:
        text = texts[collection.uuid]
    except KeyError:
        return
    text.rect.midleft = (x, y)
    text.rect.x += icon.width + gui.ratios.main_menu_folder_padding
    text.rect.y += icon.height // 1.5
    text.display()

    extra_x = text.rect.right + gui.ratios.main_menu_folder_padding
    star_icon = gui.icons['star']
    tag_icon = gui.icons['tag']

    # Draw the star icon
    if collection.metadata.pinned:
        star_icon.display((extra_x, text.rect.centery - star_icon.width // 2))
        extra_x += star_icon.width + gui.ratios.main_menu_folder_padding
    if collection.tags:
        tag_icon.display((extra_x, text.rect.centery - tag_icon.width // 2))
        extra_x += tag_icon.width + gui.ratios.main_menu_folder_padding

    rect = pe.rect.Rect(
        x, y,
        width -
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
    if document_uuid in DocumentViewer.PROBLEMATIC_DOCUMENTS:
        return
    document = gui.api.documents.get(document_uuid)
    if not document or document.provision:
        return
    try:
        gui.screens.put(DocumentViewer(gui, document_uuid))
    except CannotRenderDocument:
        pass


def open_document_debug_menu(gui: 'GUI', document: 'Document', position):
    DocumentDebugPopup.create(gui, document, position)()


def render_document(gui: 'GUI', rect: pe.Rect, texts, document: 'Document',
                    document_sync_operation: DocumentSyncProgress = None, scale=1):
    # Check if the document is being debugged and keep the debug menu open

    title_text = texts.get(document.uuid)
    if not title_text:
        return

    title_text.rect.topleft = rect.bottomleft
    title_text.rect.top += gui.ratios.main_menu_document_title_height_margin

    action = document.ensure_download_and_callback
    data = lambda: PreviewHandler.clear_for(document.uuid, lambda: open_document(gui, document.uuid))
    disabled = document.downloading

    # Start downloading the document if it's not available and not downloading
    # If the config specifies to download everything, download everything
    # In this case it will only download it when it shows up on the screen
    if gui.config.download_everything and not document.available and not document.downloading:
        document.ensure_download_and_callback(lambda: PreviewHandler.clear_for(document.uuid))

    render_button_using_text(
        gui, title_text,
        Defaults.TRANSPARENT_COLOR, Defaults.TRANSPARENT_COLOR,
        name=document.uuid + '_title_hover',
        hover_draw_action=render_full_document_title,
        hover_draw_data=(gui, texts, document.uuid),
        action=action,
        data=data,
        disabled=document.provision or disabled
    )

    # Render the notebook icon
    preview = PreviewHandler.get_preview(document, rect.size)
    if not preview:
        notebook_large: pe.Image = gui.icons['notebook_large'].copy()
        notebook_large.resize(tuple(v * scale for v in notebook_large.size))
        notebook_large_rect = pe.Rect(0, 0, *notebook_large.size)
        notebook_large_rect.center = rect.center
        notebook_large.display(notebook_large_rect.topleft)
    else:
        preview.display(rect.topleft)

    # Render the availability cloud icon
    is_problematic = document.uuid in DocumentViewer.PROBLEMATIC_DOCUMENTS
    if is_problematic or not document.available:
        if document.downloading:
            cloud_icon: pe.Image = gui.icons['cloud_download']
        elif is_problematic:
            cloud_icon: pe.Image = gui.icons['warning_circle']
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
        disabled=document.provision or disabled
    )

    if gui.config.debug:
        popup_exists = DocumentDebugPopup.EXISTING.get(id(document)) is not None
        debug_text = gui.main_menu.texts['debug']

        # Inflate a rect around the debug text
        inflated_rect = debug_text.rect.inflate(gui.ratios.pixel(20), gui.ratios.pixel(20))
        inflated_rect.topright = rect.topright
        debug_text.rect.center = inflated_rect.center

        if not popup_exists:
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
                data=(gui, document, inflated_rect.topleft)
            )
            debug_text.display()
        else:
            open_document_debug_menu(gui, document, inflated_rect.topleft)

    if document.provision and document_sync_operation:
        progress_rect = rect.copy()
        progress_rect.width -= gui.ratios.document_sync_progress_margin * 2
        progress_rect.height = gui.ratios.document_sync_progress_height
        progress_rect.midbottom = rect.midbottom
        progress_rect.bottom -= gui.ratios.document_sync_progress_margin

        outline_width = gui.ratios.pixel(3)
        pe.draw.rect(Defaults.BACKGROUND, progress_rect.inflate(outline_width, outline_width),
                     edge_rounding=gui.ratios.document_sync_progress_rounding)
        pe.draw.rect(Defaults.LINE_GRAY_LIGHT, progress_rect, edge_rounding=gui.ratios.document_sync_progress_rounding)
        # left = progress_rect.left
        if document_sync_operation and document_sync_operation.total > 0:
            progress_rect.width *= document_sync_operation.done / document_sync_operation.total
        pe.draw.rect(pe.colors.black, progress_rect, edge_rounding=gui.ratios.document_sync_progress_rounding)


def render_button_using_text(
        gui: 'GUI', text: pe.Text,
        inactive_color=Defaults.TRANSPARENT_COLOR, active_color=Defaults.BUTTON_ACTIVE_COLOR,
        *args,
        name: str = None, action=None, data=None,
        rect: pe.Rect = None,
        outline: int = None,
        outline_color: Union[Tuple[int, int, int], Tuple[int, int, int, int]] = Defaults.OUTLINE_COLOR,
        **kwargs
):
    if not rect:
        rect = gui.ratios.pad_button_rect(text.rect)
    pe.button.rect(
        rect,
        inactive_color, active_color,
        *args,
        name=name,
        action=action,
        data=data,
        **kwargs
    )
    if outline is not None and outline > 0:
        pe.draw.rect(outline_color, rect, outline)
    text.display()
    return rect


def render_header(gui: 'GUI', texts: Dict[str, pe.Text], callback, path_queue: 'Queue'):
    menu_location = gui.main_menu.menu_location

    render_button_using_text(gui, texts[menu_location], action=callback, name='main_menu.header')

    x = texts[menu_location].rect.right + gui.ratios.main_menu_path_padding
    y = texts[menu_location].rect.centery

    width = 0
    skips = 0

    # Calculate the width of the path
    for item in path_queue.queue:
        text_key = f'path_{item}'
        width += gui.icons['chevron_right'].width + texts[text_key].rect.width

    # Calculate the number of items to skip in the path, this results in the > > you see in the beginning
    while width > gui.width - (x + 200):
        skips += 1
        if len(path_queue.queue) - skips <= 0:
            # window is too small to render the path
            return
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
            render_button_using_text(gui, texts[text_key], action=callback, data=item, name=f'main_menu.path={item}')
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


def draw_bottom_loading_bar(gui: 'GUI', current: int, total: int, finish: bool = False):
    draw_bottom_bar(gui)
    bottom_bar_rect = get_bottom_bar_rect(gui)
    loading_bar_rect = pe.Rect(0, 0, gui.ratios.bottom_loading_bar_width, gui.ratios.bottom_loading_bar_height)
    loading_bar_rect.midright = bottom_bar_rect.midright
    loading_bar_rect.x -= gui.ratios.bottom_loading_bar_padding

    # Draw the loading bar background
    pe.draw.rect(Defaults.LINE_GRAY, loading_bar_rect, 0, edge_rounding=gui.ratios.bottom_loading_bar_rounding)

    if total > 0:
        loading_bar_rect.width = int(loading_bar_rect.width * current / total)

    pe.draw.rect(pe.colors.white, loading_bar_rect, 0, edge_rounding=gui.ratios.bottom_loading_bar_rounding)

    # Make and show text of current / total
    if not finish:
        text = pe.Text(f"{current} / {total}", Defaults.MAIN_MENU_PROGRESS_FONT, gui.ratios.bottom_bar_size,
                       colors=Defaults.TEXT_COLOR_H)
        text.rect.midright = loading_bar_rect.midleft
        text.rect.right -= gui.ratios.bottom_loading_bar_padding
        text.display()
    else:
        icon: pe.Image = gui.icons['cloud_synced_inverted']
        icon_rect = pe.Rect(0, 0, *icon.size)
        icon_rect.midright = loading_bar_rect.midleft
        icon_rect.right -= gui.ratios.bottom_loading_bar_padding
        icon.display(icon_rect.topleft)

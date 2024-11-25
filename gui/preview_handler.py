import os.path
import threading
from traceback import print_exc
from typing import Dict, Tuple, List, Union

import pygameextra as pe

from gui.defaults import Defaults
from gui.screens.viewer.renderers.notebook.rm_lines import Notebook_rM_Lines_Renderer
from rm_api import Document
from rm_api.models import Page
from rm_api.storage.common import FileHandle
from rm_api.storage.v3 import get_file_contents, check_file_exists

try:
    import fitz
except ImportError:
    fitz = None

MAY_CONTAIN_A_IMAGE = Union[None, pe.Image]


class PreviewHandler:
    # Document id : (page id, sprite)
    # Sprite just allows for easy resizing
    CACHED_PREVIEW: Dict[str, Tuple[str, MAY_CONTAIN_A_IMAGE]] = {}
    CACHED_RESIZES: Dict[str, pe.Image] = {}
    PREVIEW_LOAD_TASKS: List[str] = []
    PYGAME_THREAD_LOCK = threading.Lock()

    @classmethod
    def get_preview(cls, document: Document, size: Tuple[int, int]) -> MAY_CONTAIN_A_IMAGE:
        size = tuple(min(given, max) for given, max in zip(size, Defaults.PREVIEW_SIZE))
        try:
            image = cls._get_preview(document)
        except:
            print_exc()
            image = None
        if image is None:
            return None
        resized_image = cls.CACHED_RESIZES.get(document.uuid)
        if not resized_image:
            if image.size == size:
                return image
            resized_image = image.copy()
            resized_image.resize(size)
            cls.CACHED_RESIZES[document.uuid] = resized_image
        elif resized_image.size != size:
            del cls.CACHED_RESIZES[document.uuid]
            resized_image = image.copy()
            resized_image.resize(size)
            cls.CACHED_RESIZES[document.uuid] = resized_image
        return resized_image

    @classmethod
    def _get_preview(cls, document: Document) -> MAY_CONTAIN_A_IMAGE:
        try:
            if document.content.cover_page_number == -1:
                page_id = document.content.c_pages.last_opened.value
            else:
                page_id = document.content.c_pages.pages[0].id
        except:
            page_id = 'index-error'
        document_id = document.uuid
        loading_task = f'{document_id}.{page_id}'
        location = os.path.join(Defaults.THUMB_FILE_PATH, f'{loading_task}.png')
        if preview := cls.CACHED_PREVIEW.get(document_id):
            if preview[0] == page_id:
                if os.path.isdir(Defaults.THUMB_FILE_PATH):
                    if not document.provision and preview[1] and not os.path.exists(location):
                        preview[1].surface.save_to_file(location)
                return preview[1]
        # If the preview is not cached, load it
        if os.path.exists(location):
            image = pe.Image(location)
            cls.CACHED_PREVIEW[document_id] = (page_id, image)
            return cls._get_preview(document)

        # Prevent multiple of the same task
        if loading_task in cls.PREVIEW_LOAD_TASKS:
            return None

        # Create a new loading task
        cls.PREVIEW_LOAD_TASKS.append(loading_task)
        threading.Thread(target=cls.handle_loading_task, args=(loading_task, document, page_id), daemon=True).start()

    @classmethod
    def handle_loading_task(cls, loading_task, document: Document, page_id: str):
        try:
            cls._handle_loading_task(document, page_id)
        except:
            print_exc()
            cls.CACHED_PREVIEW[document.uuid] = (page_id, None)
        finally:
            cls.PREVIEW_LOAD_TASKS.remove(loading_task)

    @classmethod
    def _handle_loading_task(cls, document: Document, page_id: str):
        file = document.files_available.get(file_uuid := f'{document.uuid}/{page_id}.rm')

        base_img: pe.Surface = None

        if document.content.file_type == 'pdf':
            if page_id == 'index-error':
                page = Page.new_pdf_redirect(0, 'index-error', 'index-error')
            else:
                page = document.content.c_pages.get_page_from_uuid(page_id)

            if page and page.redirect:
                pdf_file = document.files_available.get(f'{document.uuid}.pdf')

                document.load_files_from_cache()

                if pdf_file and (stream := document.content_data.get(pdf_file.uuid)) and fitz:
                    if isinstance(stream, FileHandle):
                        pdf = fitz.open(stream.file_path, filetype='pdf')
                    else:
                        pdf = fitz.open(
                            stream=stream,
                            filetype='pdf'
                        )

                    pdf_page = pdf[page.redirect.value]

                    scale_x = Defaults.PREVIEW_SIZE[0] / pdf_page.rect.width
                    scale_y = Defaults.PREVIEW_SIZE[1] / pdf_page.rect.height
                    matrix = fitz.Matrix(scale_x, scale_y)

                    # noinspection PyUnresolvedReferences
                    pix = pdf_page.get_pixmap(matrix=matrix)
                    mode = "RGBA" if pix.alpha else "RGB"
                    # noinspection PyTypeChecker
                    base_img = pe.Surface(
                        surface=pe.pygame.image.frombuffer(pix.samples, (pix.width, pix.height), mode))

        if not document.provision:
            document.unload_files()

        file_hash = None
        if not file:
            if pe.settings.config.download_last_opened_page_to_make_preview:
                for file in document.files:
                    if file.uuid == file_uuid:
                        file_hash = file.hash
                        break
        else:
            file_hash = file.hash
        if file_hash and check_file_exists(document.api, file_hash):
            rm_bytes = get_file_contents(document.api, file_hash, binary=True)
            if not rm_bytes:
                raise Exception('Page content unavailable to construct preview')
            image = Notebook_rM_Lines_Renderer.generate_expanded_notebook_from_rm(document.metadata, rm_bytes,
                                                                                  use_lock=cls.PYGAME_THREAD_LOCK).get_frame_from_initial(
                0, 0)
            image.resize(Defaults.PREVIEW_SIZE)
        else:
            image = None

        if base_img:
            if image:
                base_img.stamp(image.surface)
                image.surface = base_img
            else:
                image = pe.Image(base_img)

        cls.CACHED_PREVIEW[document.uuid] = (page_id, image)
        if cls.CACHED_RESIZES.get(document.uuid):
            del cls.CACHED_RESIZES[document.uuid]

    @classmethod
    def clear_for(cls, document_uuid: str, callback=None):
        cls.CACHED_PREVIEW.pop(document_uuid, None)
        if callback:
            callback()

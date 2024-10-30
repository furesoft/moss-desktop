import threading
from traceback import print_exc
from typing import Dict, Tuple, List, Union

import pygameextra as pe

from gui.screens.viewer.renderers.notebook.rm_lines import Notebook_rM_Lines_Renderer
from rm_api import Document
from rm_api.storage.v3 import get_file_contents

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
        try:
            image = cls._get_preview(document)
        except:
            image = None
        if image is None:
            return None
        resized_image = cls.CACHED_RESIZES.get(document.uuid)
        if not resized_image:
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
        if document.content.cover_page_number == -1:
            page_id = document.content.c_pages.last_opened.value
        else:
            page_id = document.content.c_pages.pages[0].id
        document_id = document.uuid
        if preview := cls.CACHED_PREVIEW.get(document_id):
            if preview[0] == page_id:
                return preview[1]
        # If the preview is not cached, load it
        loading_task = f'{document_id}/{page_id}'

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
            cls.CACHED_PREVIEW[document.uuid] = (page_id, None)
        finally:
            cls.PREVIEW_LOAD_TASKS.remove(loading_task)

    @classmethod
    def _handle_loading_task(cls, document: Document, page_id: str):
        if not document.available and not pe.settings.config.download_last_opened_page_to_make_preview:
            # Wait for the document to be available
            return
        
        file = document.files_available.get(file_uuid := f'{document.uuid}/{page_id}.rm')

        if not file:
            if pe.settings.config.download_last_opened_page_to_make_preview:
                for file in document.files:
                    if file.uuid == file_uuid:
                        file_hash = file.hash
                        break
                else:
                    raise Exception('Could not get the file to construct preview')
            else:
                raise Exception('The file is not available to construct preview')
        else:
            file_hash = file.hash
        
        rm_bytes = get_file_contents(document.api, file_hash, binary=True)
        if not rm_bytes:
            raise Exception('Page content unavailable to construct preview')
        image = Notebook_rM_Lines_Renderer.generate_expanded_notebook_from_rm(document.metadata, rm_bytes, use_lock=cls.PYGAME_THREAD_LOCK).get_frame_from_initial(0, 0)

        cls.CACHED_PREVIEW[document.uuid] = (page_id, image)
        if cls.CACHED_RESIZES.get(document.uuid):
            del cls.CACHED_RESIZES[document.uuid]


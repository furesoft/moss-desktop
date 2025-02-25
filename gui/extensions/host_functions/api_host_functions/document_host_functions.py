from typing import Annotated

from box import Box
from extism import Json

from rm_api import Document
from rm_api.storage.common import FileHandle
from .import_types import DocumentNewNotebook, DocumentNewPDF, DocumentNewEPUB
from .. import definitions as d


@d.host_fn()
def moss_api_document_new_notebook(value: Annotated[DocumentNewNotebook, Json]) -> str:
    _ = Box(value)
    notebook_data_paths = d.extension_manager.organize_paths(_.notebook_data)
    document = Document.new_notebook(
        d.api, _.name, _.parent, _.document_uuid,
        _.page_count, [FileHandle(path) for path in notebook_data_paths],
        d.extension_manager.metadata_objects[_.metadata_id] if _.metadata_id else None,
        d.extension_manager.content_objects[_.content_id] if _.content_id else None,
    )
    d.api.documents[document.uuid] = document
    return document.uuid


@d.host_fn()
def moss_api_document_new_pdf(value: Annotated[DocumentNewPDF, Json]) -> str:
    _ = Box(value)
    pdf_data = d.extension_manager.organize_path(_.pdf_data)
    document = Document.new_pdf(
        d.api, _.name, FileHandle(pdf_data), _.parent, _.document_uuid
    )
    d.api.documents[document.uuid] = document
    return document.uuid


@d.host_fn()
def moss_api_document_new_epub(value: Annotated[DocumentNewEPUB, Json]) -> str:
    _ = Box(value)
    epub_data = d.extension_manager.organize_path(_.epub_data)
    document = Document.new_epub(
        d.api, _.name, FileHandle(epub_data), _.parent, _.document_uuid
    )
    d.api.documents[document.uuid] = document
    return document.uuid

# @d.host_fn()
# def moss_api_document_duplicate():
#     ...
#
#
# @d.host_fn()
# def moss_api_document_randomize_uuids():
#     ...
#
#
# @d.host_fn()
# def moss_api_document_unload_files():
#     ...
#
#
# @d.host_fn()
# def moss_api_document_load_files_from_cache():
#     ...
#
#
# @d.host_fn()
# def moss_api_document_ensure_download_and_callback():
#     ...
#
#
# @d.host_fn()
# def moss_api_document_ensure_download():
#     ...
#
#
# @d.host_fn()
# def moss_api_document_export():
#     ...

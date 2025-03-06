from functools import partial
from typing import List, Annotated

from extism import Json

import rm_api
from rm_api import Document, FileSyncProgress
from .shared_types import TRM_RootInfo, TRM_FileList
from .wrappers import many_document_wrapper, document_wrapper, file_sync_progress_wrapper
from .. import definitions as d


@d.host_fn()
def moss_api_get_root() -> Annotated[TRM_RootInfo, Json]:
    return d.api.get_root()


@d.host_fn()
@document_wrapper()
def moss_api_upload(item: Document, callback: str, unload: bool) -> int:
    task_id = d.make_task_id()
    d.api.upload(
        item,
        partial(d.extension_manager.action(callback), task_id) if callback else None,
        unload or False
    )
    return task_id


@d.host_fn()
@many_document_wrapper()
def moss_api_upload_many_documents(items: List[Document], callback: str, unload: bool) -> int:
    task_id = d.make_task_id()
    d.api.upload_many_documents(
        items,
        partial(d.extension_manager.action(callback), task_id) if callback else None,
        unload or False
    )
    return task_id


@d.host_fn()
@document_wrapper()
def moss_api_delete(item: Document, callback: str, unload: bool) -> int:
    task_id = d.make_task_id()
    d.api.delete(
        item,
        partial(d.extension_manager.action(callback), task_id) if callback else None,
        unload or False
    )
    return task_id


@d.host_fn()
@many_document_wrapper()
def moss_api_delete_many_documents(items: List[Document], callback: str, unload: bool) -> int:
    task_id = d.make_task_id()
    d.api.delete_many_documents(
        items,
        partial(d.extension_manager.action(callback), task_id) if callback else None,
        unload or False
    )
    return task_id


@d.host_fn()
def moss_api_new_file_sync_progress() -> int:
    new = rm_api.FileSyncProgress()
    d.extension_manager.file_sync_progress_objects.append(new)
    return id(new)


@d.host_fn()
@file_sync_progress_wrapper("file_sync_progress_accessor")
def moss_api_new_document_sync_progress(item: FileSyncProgress, document_uuid: str) -> int:
    new = rm_api.DocumentSyncProgress(document_uuid, item)
    d.extension_manager.document_sync_progress_objects.append(new)
    return id(new)


@d.host_fn()
def moss_api_get_file(file_hash: str, use_cache: bool) -> Annotated[TRM_FileList, Json]:
    version, files = rm_api.get_file(d.api, file_hash, use_cache)
    return {
        'version': version,
        'files': files
    }

# @d.host_fn()
# def moss_api_put_file(file: Annotated[TRM_File, Json], data: str, sync_event: Annotated[AccessorInstance, Json]):
#     document_sync_event, _ = document_sync_progress_inferred(Box(sync_event))
#     rm_api.put_file(
#         d.api, File, base64.decode(data), document_sync_event
#     )

# @d.host_fn()
# def moss_api_get_file_contents():
#     ...
#
#
# @d.host_fn()
# def moss_api_check_file_exists():
#     ...
#
#
# @d.host_fn()
# def moss_api_update_root():
#     ...

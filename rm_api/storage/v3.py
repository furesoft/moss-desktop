import base64
import json
import os
from hashlib import sha256
from traceback import format_exc

import httpx
from colorama import Fore, Style
from crc32c import crc32c
from functools import lru_cache
from json import JSONDecodeError

from httpx import HTTPTransport

import rm_api.models as models
from typing import TYPE_CHECKING, Union, Tuple, List

from rm_api.notifications.models import DocumentSyncProgress
from rm_api.storage.exceptions import NewSyncRequired

FILES_URL = "{0}sync/v3/files/{1}"

if TYPE_CHECKING:
    from rm_api import API
    from rm_api.models import File

DEFAULT_ENCODING = 'utf-8'
EXTENSION_ORDER = ['content', 'metadata', 'rm']


def get_file_item_order(item: 'File'):
    try:
        return EXTENSION_ORDER.index(item.uuid.rsplit('.', 1)[-1])
    except ValueError:
        return -1


def make_storage_request(api: 'API', method, request, data: dict = None) -> Union[str, None, dict]:
    response = api.session.request(
        method,
        request.format(api.document_storage_uri),
        json=data or {},
    )

    if response.status_code == 400:
        api.use_new_sync = True
        raise NewSyncRequired()
    if response.status_code != 200:
        print(response.text, response.status_code)
        return None
    try:
        return response.json()
    except JSONDecodeError:
        return response.text


@lru_cache
def make_files_request(api: 'API', method, file, data: dict = None, binary: bool = False, use_cache: bool = True) -> \
        Union[str, None, dict, bool, bytes]:
    if method == 'HEAD':
        method = 'GET'
        head = True
    else:
        head = False
    if api.sync_file_path:
        location = os.path.join(api.sync_file_path, file)
    else:
        location = None
    if use_cache and location and os.path.exists(location):
        if head:
            return True
        if binary:
            with open(location, 'rb') as f:
                return f.read()
        else:
            with open(location, 'r', encoding=DEFAULT_ENCODING) as f:
                data = f.read()
            try:
                return json.loads(data)
            except JSONDecodeError:
                return data
    response = api.session.request(
        method,
        FILES_URL.format(api.document_storage_uri, file),
        json=data or None,
        stream=head,
        allow_redirects=not head
    )
    if head and response.status_code in (302, 404, 200):
        return response.status_code != 404
    if response.content == b'{"message":"invalid hash"}\n':
        return None
    elif not response.ok:
        raise Exception(f"Failed to make files request - {response.status_code}\n{response.text}")
    if binary:
        if location:
            with open(location, "wb") as f:
                f.write(response.content)
        return response.content
    else:
        if location:
            with open(location, "w", encoding=DEFAULT_ENCODING) as f:
                f.write(response.text)
        try:
            return response.json()
        except JSONDecodeError:
            return response.text


def put_file(api: 'API', file: 'File', data: bytes, sync_event: DocumentSyncProgress):
    checksum_bs4 = base64.b64encode(crc32c(data).to_bytes(4, 'big')).decode('utf-8')
    content_length = len(data)

    position = 0

    def file_chunk_generator(chunk_size=int(4e+6)):
        nonlocal sync_event, data, content_length, position
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            sync_event.done += len(chunk)  # Update progress
            yield chunk
            position += len(chunk)

    with httpx.Client(http2=False, transport=HTTPTransport(retries=api.http_adapter.max_retries.total)) as request:
        sync_event.total += content_length
        sync_event.add_task()

        # Try uploading through remarkable
        try:
            response = request.put(
                FILES_URL.format(api.document_storage_uri, file.hash),
                content=file_chunk_generator(),
                headers=(headers := {
                    **api.session.headers,
                    'content-length': str(content_length),
                    'content-type': 'application/octet-stream',
                    'rm-filename': file.rm_filename,
                    'x-goog-hash': f'crc32c={checksum_bs4}'
                })
            )
        except:
            api.log(format_exc())
            return False

        if response.status_code == 302:
            # Reset progress, start uploading through google instead
            sync_event.done -= position

            try:
                response = request.put(
                    response.headers['location'],
                    content=file_chunk_generator(),
                    headers={
                        **headers,
                        'x-goog-content-length-range': response.headers['x-goog-content-length-range'],
                        'x-goog-hash': f'crc32c={checksum_bs4}'
                    }
                )
            except:
                api.log(format_exc())
                return False

        if response.status_code != 200:
            api.log(f"Put file failed - {response.status_code}\n{response.text}")
            return False
        else:
            api.log(file.uuid, "uploaded")

        sync_event.finish_task()
        return True


def get_file(api: 'API', file, use_cache: bool = True, raw: bool = False) -> Tuple[int, Union[List['File'], List[str]]]:
    res = make_files_request(api, "GET", file, use_cache=use_cache)
    if isinstance(res, int):
        return res, []
    version, *lines = res.splitlines()
    if raw:
        return version, lines
    return version, [models.File.from_line(line) for line in lines]


def get_file_contents(api: 'API', file, binary: bool = False, use_cache: bool = True) -> Union[str, None, dict]:
    return make_files_request(api, "GET", file, binary=binary, use_cache=use_cache)


def check_file_exists(api: 'API', file, binary: bool = False, use_cache: bool = True) -> Union[str, None, dict]:
    return make_files_request(api, "HEAD", file, binary=binary, use_cache=use_cache)


def get_documents_using_root(api: 'API', progress, root):
    try:
        _, files = get_file(api, root)
    except:
        from rm_api.storage.old_sync import update_root
        print(f"{Fore.RED}{Style.BRIGHT}AN ISSUE OCCURRED GETTING YOUR ROOT INDEX!{Fore.RESET}{Style.RESET_ALL}")

        root = api.get_root()

        new_root = {
            "broadcast": True,
            "generation": root['generation']
        }

        root_file_content = b'3\n'

        root_file = models.File(models.make_hash(root_file_content), f"root.docSchema", 0, len(root_file_content))
        new_root['hash'] = root_file.hash
        put_file(api, root_file, root_file_content, DocumentSyncProgress(''))
        update_root(api, new_root)
        _, files = get_file(api, new_root['hash'])
    deleted_document_collections_list = set(api.document_collections.keys())
    deleted_documents_list = set(api.documents.keys())
    document_collections_with_items = set()
    badly_hashed = []

    total = len(files)

    for i, file in enumerate(files):
        _, file_content = get_file(api, file.hash)
        content = None

        # Check the hash in case it needs fixing
        document_file_hash = sha256()
        for item in sorted(file_content, key=lambda item: file.uuid):
            document_file_hash.update(bytes.fromhex(item.hash))
        expected_hash = document_file_hash.hexdigest()
        matches_hash = file.hash == expected_hash

        file_content.sort(key=get_file_item_order)
        for item in file_content:
            if item.uuid == f'{file.uuid}.content':
                try:
                    content = get_file_contents(api, item.hash)
                except:
                    break
                if not isinstance(content, dict):
                    break
            if item.uuid == f'{file.uuid}.metadata':
                if (old_document_collection := api.document_collections.get(file.uuid)) is not None:
                    if api.document_collections[file.uuid].metadata.hash == item.hash:
                        if file.uuid in deleted_document_collections_list:
                            deleted_document_collections_list.remove(file.uuid)
                        if old_document_collection.uuid not in document_collections_with_items:
                            old_document_collection.has_items = False
                        if (parent_document_collection := api.document_collections.get(
                                old_document_collection.parent)) is not None:
                            parent_document_collection.has_items = True
                        else:
                            document_collections_with_items.add(old_document_collection.parent)
                        continue
                elif (old_document := api.documents.get(file.uuid)) is not None:
                    if api.documents[file.uuid].metadata.hash == item.hash:
                        if file.uuid in deleted_documents_list:
                            deleted_documents_list.remove(file.uuid)
                        if (parent_document_collection := api.document_collections.get(
                                old_document.parent)) is not None:
                            parent_document_collection.has_items = True
                        document_collections_with_items.add(old_document.parent)
                        continue
                try:
                    metadata = models.Metadata(get_file_contents(api, item.hash), item.hash)
                except:
                    continue
                if metadata.type == 'CollectionType':
                    if content is not None:
                        tags = content.get('tags', ())
                    else:
                        tags = ()
                    api.document_collections[file.uuid] = models.DocumentCollection(
                        [models.Tag(tag) for tag in tags],
                        metadata, file.uuid
                    )

                    if file.uuid in document_collections_with_items:
                        api.document_collections[file.uuid].has_items = True

                    if (parent_document_collection := api.document_collections.get(
                            api.document_collections[file.uuid].parent)) is not None:
                        parent_document_collection.has_items = True
                    document_collections_with_items.add(api.document_collections[file.uuid].parent)

                    if file.uuid in deleted_document_collections_list:
                        deleted_document_collections_list.remove(file.uuid)
                    break
                elif metadata.type == 'DocumentType':
                    api.documents[file.uuid] = models.Document(api, models.Content(content, item.hash, api.debug),
                                                               metadata, file_content, file.uuid)
                    if not matches_hash:
                        badly_hashed.append(api.documents[file.uuid])
                    if (parent_document_collection := api.document_collections.get(
                            api.documents[file.uuid].parent)) is not None:
                        parent_document_collection.has_items = True
                    document_collections_with_items.add(api.documents[file.uuid].parent)
                    if file.uuid in deleted_documents_list:
                        deleted_documents_list.remove(file.uuid)
                    break
        progress(i + 1, total)
    else:
        i = 0

    if badly_hashed:
        print(f"{Fore.YELLOW}Warning, fixing some bad document tree hashes!{Fore.RESET}")
        api.upload_many_documents(badly_hashed)

    total += len(deleted_document_collections_list) + len(deleted_documents_list)

    for j, uuid in enumerate(deleted_document_collections_list):
        del api.document_collections[uuid]
        progress(i + j + 1, total)
    else:
        j = 0

    for k, uuid in enumerate(deleted_documents_list):
        try:
            if not api.documents[uuid].provision:
                del api.documents[uuid]
        except KeyError:
            pass
        progress(i + j + k + 1, total)

import json
import os
from json import JSONDecodeError
from typing import TYPE_CHECKING, Union, List, Tuple

from urllib3.exceptions import DecodeError
import rm_api.models as models
from rm_api.storage.exceptions import NewSyncRequired
from rm_api.storage.new_sync import get_documents_new_sync

if TYPE_CHECKING:
    from rm_api import API
    from rm_api.models import *

DOCUMENT_STORAGE_URL = "{0}service/json/1/document-storage?environment=production&group=auth0%7C5a68dc51cb30df3877a1d7c4&apiVer=2"
SYNC_ROOT_URL = "{0}sync/v3/root"
FILES_URL = "{0}sync/v3/files/{1}"
TEMP = "sync"

os.makedirs(TEMP, exist_ok=True)


def get_document_storage(api: 'API'):
    response = api.session.get(DOCUMENT_STORAGE_URL.format(api.discovery_uri))
    return response.json().get("Host")


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


def make_files_request(api: 'API', method, file, data: dict = None, binary: bool = False) -> Union[str, None, dict]:
    location = os.path.join(TEMP, file)
    if os.path.exists(location):
        if binary:
            with open(location, 'rb') as f:
                return f.read()
        else:
            with open(location, 'r') as f:
                data = f.read()
            try:
                return json.loads(data)
            except JSONDecodeError:
                return data
    response = api.session.request(
        method,
        FILES_URL.format(api.document_storage_uri, file),
        json=data or {},
    )
    if response.status_code != 200:
        print(response.text, response.status_code)
        return None
    if binary:
        with open(location, "wb") as f:
            f.write(response.content)
        return response.content
    else:
        with open(location, "w") as f:
            f.write(response.text)
        try:
            return response.json()
        except JSONDecodeError:
            return response.text


def get_file(api: 'API', file) -> Tuple[int, List['File']]:
    version, *lines = make_files_request(api, "GET", file).splitlines()
    return version, [models.File.from_line(line) for line in lines]


def get_file_contents(api: 'API', file, binary: bool = False) -> Union[str, None, dict]:
    return make_files_request(api, "GET", file, binary=binary)


def get_root(api: 'API'):
    return make_storage_request(api, "GET", SYNC_ROOT_URL)


def get_documents_old_sync(api: 'API', progress):
    try:
        root = get_root(api)['hash']
    except NewSyncRequired:
        return get_documents_new_sync(api, progress)
    _, files = get_file(api, root)
    document_collections = {}
    documents = {}
    for i, file in enumerate(files):
        _, file_content = get_file(api, file.hash)
        content = None
        for item in file_content:
            if item.uuid == f'{file.uuid}.content':
                content = get_file_contents(api, item.hash)
            if item.uuid == f'{file.uuid}.metadata':
                metadata = models.Metadata(get_file_contents(api, item.hash))
                if metadata.type == 'CollectionType':
                    document_collections[file.uuid] = models.DocumentCollection(
                        [models.Tag(tag) for tag in content['tags']],
                        metadata, file.uuid
                    )
                elif metadata.type == 'DocumentType':
                    documents[file.uuid] = models.Document(api, content, metadata, file_content, file.uuid)
        progress(i + 1, len(files))

    return document_collections, documents

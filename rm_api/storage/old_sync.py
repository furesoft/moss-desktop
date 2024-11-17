import base64
import json
import os
from json import JSONDecodeError
from typing import TYPE_CHECKING, Union, List, Tuple

from crc32c import crc32c
from urllib3.exceptions import DecodeError
import rm_api.models as models
from rm_api.notifications.models import APIFatal
from rm_api.storage.exceptions import NewSyncRequired
from rm_api.storage.new_sync import get_documents_new_sync
from rm_api.storage.v3 import make_storage_request, get_documents_using_root, check_file_exists

if TYPE_CHECKING:
    from rm_api import API
    from rm_api.models import *

SYNC_ROOT_URL = "{0}sync/v3/root"


def get_root(api: 'API'):
    return make_storage_request(api, "GET", SYNC_ROOT_URL)


class RootUploadFailure(Exception):
    """This happens if it was updated by another process"""
    def __init__(self):
        super().__init__("Failed to update root")


def update_root(api: 'API', root: dict):
    data = json.dumps(root, indent=4).encode('utf-8')
    checksum_bs4 = base64.b64encode(crc32c(data).to_bytes(4, 'big')).decode('utf-8')
    print(root['hash'])
    exists = check_file_exists(api, root['hash'], use_cache=False)
    if not exists and not api.ignore_error_protection:
        api.spread_event(APIFatal())
        raise Exception("The root file attempted to be set was not on the server")
    response = api.session.put(
        SYNC_ROOT_URL.format(api.document_storage_uri),
        data=data,
        headers={
            **api.session.headers,
            'rm-filename': 'roothash',
            'Content-Type': 'application/json',
            'x-goog-hash': f'crc32c={checksum_bs4}',
        },
    )

    if not response.ok:
        raise RootUploadFailure()
    else:
        api.log("Root updated:", response.json())
    return True



def get_documents_old_sync(api: 'API', progress):
    root = get_root(api)['hash']
    return get_documents_using_root(api, progress, root)

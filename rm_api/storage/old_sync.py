import json
import os
from json import JSONDecodeError
from typing import TYPE_CHECKING, Union, List, Tuple

from urllib3.exceptions import DecodeError
import rm_api.models as models
from rm_api.storage.exceptions import NewSyncRequired
from rm_api.storage.new_sync import get_documents_new_sync
from rm_api.storage.v3 import make_storage_request, get_documents_using_root

if TYPE_CHECKING:
    from rm_api import API
    from rm_api.models import *

SYNC_ROOT_URL = "{0}sync/v3/root"


def get_root(api: 'API'):
    return make_storage_request(api, "GET", SYNC_ROOT_URL)


def get_documents_old_sync(api: 'API', document_collections, documents, progress):
    root = get_root(api)['hash']
    return get_documents_using_root(api, document_collections, documents, progress, root)


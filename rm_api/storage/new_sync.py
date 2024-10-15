from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rm_api import API
    from rm_api.models import *

SYNC_ROOT_URL = "{0}document-storage/json/2/docs"


def get_root(api: 'API') -> dict:
    return api.session.get(SYNC_ROOT_URL.format(api.document_storage_uri))


def get_documents_new_sync(api: 'API', progress):
    root = get_root(api)
    # TODO: Figure out why we get a server error
    print(root.text)
    exit()

from io import IOBase
from typing import TYPE_CHECKING

DOCUMENT_STORAGE_URL = "{0}service/json/1/document-storage?environment=production&group=auth0%7C5a68dc51cb30df3877a1d7c4&apiVer=2"
DOCUMENT_NOTIFICATIONS_URL = "{0}service/json/1/notifications?environment=production&group=auth0%7C5a68dc51cb30df3877a1d7c4&apiVer=1"

if TYPE_CHECKING:
    from rm_api import API, FileSyncProgress, DocumentSyncProgress


def get_document_storage_uri(api: 'API'):
    response = api.session.get(DOCUMENT_STORAGE_URL.format(api.discovery_uri))
    host = response.json().get("Host")
    secure = 'https'
    if host == 'local.appspot.com':
        secure, root_host = api.uri.split('://')
        root_host = root_host.split("/")[0]
    else:
        root_host = host
    root_response = api.session.get(f"{secure}://{root_host}/sync/v3/root")
    if not root_response.ok:
        api.use_new_sync = True
        return None
    return host


def get_document_notifications_uri(api: 'API'):
    response = api.session.get(DOCUMENT_NOTIFICATIONS_URL.format(api.discovery_uri))
    host = response.json().get("Host")
    if host == 'local.appspot.com':
        host = api.uri.split("://")[1].split("/")[0]
    return host


class ProgressFileAdapter(IOBase):
    def __init__(self, document_sync: 'DocumentSyncProgress', file_sync: 'FileSyncProgress', data: bytes):
        self.document_sync = document_sync
        self.file_sync = file_sync
        self.data = data

    def read(self, size=-1):
        if size < 0:
            raise ValueError("The size argument is required and must be non-negative.")

        index = self.file_sync.done
        chunk = self.data[index:index + size]
        self.file_sync.done += len(chunk)
        self.document_sync.done += len(chunk)
        return chunk

    def __len__(self):
        return self.file_sync.total

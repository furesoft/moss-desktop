import json
import os
import uuid
from hashlib import sha256
from io import BytesIO
from traceback import print_exc
from typing import Dict, List

import requests
import colorama

from rm_api.auth import get_token, refresh_token
from rm_api.models import DocumentCollection, Document, Metadata, Content, make_uuid, File, make_hash
from rm_api.notifications import handle_notifications
from rm_api.notifications.models import FileSyncProgress
from rm_api.storage.common import get_document_storage_uri, get_document_notifications_uri
from rm_api.storage.new_sync import get_documents_new_sync, handle_new_api_steps
from rm_api.storage.old_sync import get_documents_old_sync, update_root
from rm_api.storage.new_sync import get_root as get_root_new
from rm_api.storage.old_sync import get_root as get_root_old
from rm_api.storage.v3 import get_documents_using_root, get_file, get_file_contents, make_files_request, put_file
from rm_lines.blocks import write_blocks, blank_document

colorama.init()


class API:
    document_collections: Dict[str, DocumentCollection]
    documents: Dict[str, Document]

    def __init__(self, require_token: bool = True, token_file_path: str = 'token', sync_file_path: str = 'sync',
                 uri: str = None, discovery_uri: str = None, author_id: str = None):
        self.session = requests.Session()
        self.token_file_path = token_file_path
        if not author_id:
            self.author_id = make_uuid()
        else:
            self.author_id = author_id
        self.uri = uri or os.environ.get("URI", "https://webapp.cloud.remarkable.com/")
        self.discovery_uri = discovery_uri or os.environ.get("DISCOVERY_URI",
                                                             "https://service-manager-production-dot-remarkable-production.appspot.com/")
        self.sync_file_path = sync_file_path
        if self.sync_file_path is not None:
            os.makedirs(self.sync_file_path, exist_ok=True)
        self.document_storage_uri = None
        self.document_notifications_uri = None
        self._hook_list = {}  # Used for event hooks
        self._use_new_sync = False
        # noinspection PyTypeChecker
        self.document_collections = {}
        # noinspection PyTypeChecker
        self.documents = {}
        self._token = None
        self.debug = False
        self.connected_to_notifications = False
        self.require_token = require_token
        if not self.uri.endswith("/"):
            self.uri += "/"
        if not self.discovery_uri.endswith("/"):
            self.discovery_uri += "/"
        token = os.environ.get("TOKEN")
        if token is None:
            if os.path.exists(self.token_file_path):
                self.token = open(self.token_file_path).read()
            else:
                self.get_token()
        else:
            self.token = token

    @property
    def use_new_sync(self):
        return self._use_new_sync

    def connect_to_notifications(self):
        if self.connected_to_notifications:
            return
        self.check_for_document_notifications()
        handle_notifications(self)
        self.connected_to_notifications = True

    @use_new_sync.setter
    def use_new_sync(self, value):
        if not self._use_new_sync and value:
            handle_new_api_steps(self)
        self._use_new_sync = value

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, value):
        if not value:
            return
        token = refresh_token(self, value)
        self.session.headers["Authorization"] = f"Bearer {token}"
        self._token = token

    def get_token(self, code: str = None):
        self.token = get_token(self, code)

    def get_documents(self, progress=lambda d, i: None):
        self.check_for_document_storage()
        if self.use_new_sync:
            get_documents_new_sync(self, progress)
        else:
            get_documents_old_sync(self, progress)

    def get_root(self):
        self.check_for_document_storage()
        if self.use_new_sync:
            return get_root_new(self)
        else:
            return get_root_old(self)

    def spread_event(self, event: object):
        for hook in self._hook_list.values():
            hook(event)

    def add_hook(self, hook_id, hook):
        self._hook_list[hook_id] = hook

    def remove_hook(self, hook_id):
        del self._hook_list[hook_id]

    def check_for_document_storage(self):
        if not self.document_storage_uri:
            uri = get_document_storage_uri(self)
            if not uri:
                return
            elif uri == 'local.appspot.com':
                uri = self.uri
            else:
                if not uri.endswith("/"):
                    uri += "/"
                uri = f'https://{uri}'
            self.document_storage_uri = uri

    def upload(self, document: Document):
        upload_event = FileSyncProgress()
        self.spread_event(upload_event)
        try:
            document.ensure_download()
            self._upload_document_contents(document, upload_event)
        finally:
            upload_event.finished = True

    def upload_many_documents(self, documents: List[Document], callback=None):
        upload_event = FileSyncProgress()
        self.spread_event(upload_event)
        try:
            for document in documents:
                document.ensure_download()
                self._upload_document_contents(document, upload_event)
        finally:
            upload_event.finished = True

    def _upload_document_contents(self, document: Document, progress: FileSyncProgress):
        # We need to upload the content, metadata, rm file, file list and update root
        # This is the order that remarkable expects the upload to happen in, anything else and they might detect it as
        # API tampering, so we wanna follow their upload cycle
        progress.total += 2  # Getting root / Uploading root

        root = self.get_root()  # root info

        _, files = get_file(self, root['hash'])
        progress.done += 1  # Got root

        new_root = {
            "broadcast": True,
            "generation": root['generation']
        }

        document_file = File(
            None,
            document.uuid,
            len(document.files), 0,
            f"{document.uuid}.docSchema"
        )

        new_root_files = [document_file] + [
            file
            for file in files
            if file.uuid != document.uuid
        ]

        old_files = []
        files_with_changes = []

        document.export()

        # Figure out what files have changed
        for file in document.files:
            try:
                old_content = get_file_contents(self, file.hash, binary=True, use_cache=False)
                if old_content != document.content_data[file.uuid]:
                    files_with_changes.append(file)
                else:
                    old_files.append(file)
            except:
                files_with_changes.append(file)

        # Copy the content data so we can add more files to it
        content_data = document.content_data.copy()

        # Update the hash for files that have changed
        for file in files_with_changes:
            file.hash = make_hash(content_data[file.uuid])
            file.size = len(content_data[file.uuid])

        # Make a new document file with the updated files for this document
        document_file_content = ['3\n']
        document_file_hash = sha256()

        for file in sorted(document.files, key=lambda file: file.uuid):
            file.hash = make_hash(content_data[file.uuid])
            document_file_hash.update(bytes.fromhex(file.hash))
            file.size = len(content_data[file.uuid])
            document_file_content.append(file.to_line())

        document_file_content = ''.join(document_file_content).encode()
        document_file.hash = document_file_hash.hexdigest()
        document_file.size = len(document_file_content)

        # Add the document file to the content_data
        content_data[document_file.uuid] = document_file_content
        files_with_changes.append(document_file)

        # Prepare the root file
        root_file_content = ['3\n']
        for file in new_root_files:
            root_file_content.append(file.to_root_line())

        root_file_content = ''.join(root_file_content).encode()
        root_file = File(make_hash(root_file_content), f"root.docSchema", len(new_root_files), len(root_file_content))
        new_root['hash'] = root_file.hash

        files_with_changes.append(root_file)
        content_data[root_file.uuid] = root_file_content

        # Upload all the files that have changed
        progress.total += len(files_with_changes)

        for file in files_with_changes:
            put_file(self, file, content_data[file.uuid])
            progress.done += 1

        # Update the root
        update_root(self, new_root)
        progress.done += 1  # Update done finally matching done/total

    def check_for_document_notifications(self):
        if not self.document_notifications_uri:
            uri = get_document_notifications_uri(self)
            if not uri:
                return
            elif uri == 'local.appspot.com':
                uri = self.uri
            else:
                if not uri.endswith("/"):
                    uri += "/"
                uri = f'https://{uri}'
            self.document_notifications_uri = uri

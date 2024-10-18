import os
from typing import Dict

import requests
import colorama

from rm_api.auth import get_token, refresh_token
from rm_api.models import DocumentCollection, Document
from rm_api.notifications import handle_notifications
from rm_api.storage.common import get_document_storage_uri, get_document_notifications_uri
from rm_api.storage.new_sync import get_documents_new_sync, handle_new_api_steps
from rm_api.storage.old_sync import get_documents_old_sync

colorama.init()


class API:
    document_collections: Dict[str, DocumentCollection]
    documents: Dict[str, Document]

    def __init__(self, require_token: bool = True, token_file_path: str = 'token', sync_file_path: str = 'sync'):
        self.session = requests.Session()
        self.token_file_path = token_file_path
        self.uri = os.environ.get("URI", "https://webapp.cloud.remarkable.com/")
        self.discovery_uri = os.environ.get("DISCOVERY_URI",
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

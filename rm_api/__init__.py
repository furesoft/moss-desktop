import os
from typing import Dict

import requests

from rm_api.auth import get_token, refresh_token
from rm_api.models import DocumentCollection, Document
from rm_api.storage.common import get_document_storage
from rm_api.storage.new_sync import get_documents_new_sync, handle_new_api_steps
from rm_api.storage.old_sync import get_documents_old_sync


class API:
    document_collections: Dict[str, DocumentCollection]
    documents: Dict[str, Document]

    def __init__(self):
        self.session = requests.Session()
        self.uri = os.environ.get("URI", "https://webapp.cloud.remarkable.com/")
        self.discovery_uri = os.environ.get("DISCOVERY_URI", "https://service-manager-production-dot-remarkable-production.appspot.com/")
        self.document_storage_uri = None
        self._use_new_sync = False
        # noinspection PyTypeChecker
        self.document_collections = None
        # noinspection PyTypeChecker
        self.documents = None
        self._token = None
        if not self.uri.endswith("/"):
            self.uri += "/"
        if not self.discovery_uri.endswith("/"):
            self.discovery_uri += "/"
        token = os.environ.get("TOKEN")
        if token is None:
            if os.path.exists("token"):
                self.token = open("token").read()
            else:
                self.get_token()
        else:
            self.token = token

    @property
    def use_new_sync(self):
        return self._use_new_sync

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
        token = refresh_token(self, value)
        self.session.headers["Authorization"] = f"Bearer {token}"
        self._token = token

    def get_token(self):
        self.token = get_token(self)

    def get_documents(self, progress=lambda d, i: None):
        self.check_for_document_storage()
        if self.use_new_sync:
            self.document_collections, self.documents = get_documents_new_sync(self, progress)
        else:
            self.document_collections, self.documents = get_documents_old_sync(self, progress)
        return

    def check_for_document_storage(self):
        if not self.document_storage_uri:
            uri = get_document_storage(self)
            if uri == 'local.appspot.com':
                uri = self.uri
            else:
                if not uri.endswith("/"):
                    uri += "/"
                uri = f'https://{uri}'
            self.document_storage_uri = uri

import os.path
import threading
from typing import List, TYPE_CHECKING

from colorama import Fore

from rm_api.storage.v3 import get_file_contents

if TYPE_CHECKING:
    from rm_api import API


class File:
    def __init__(self, file_hash, file_uuid, content_count, file_size):
        self.hash = file_hash
        self.uuid = file_uuid
        self.content_count = content_count
        self.size = file_size

    @classmethod
    def from_line(cls, line):
        file_hash, _, file_uuid, content_count, file_size = line.split(':')
        return cls(file_hash, file_uuid, content_count, file_size)

    def __repr__(self):
        return f'{self.uuid} ({self.size})[{self.content_count}]'

    def __str__(self):
        return self.__repr__()


class Metadata:
    def __init__(self, metadata: dict, hash: str):
        self.hash = hash
        self.__metadata = metadata
        self.type = metadata['type']
        self.parent = metadata['parent'] or None
        self.pinned = metadata['pinned']
        self.created_time = metadata.get('createdTime')
        self.last_modified = metadata['lastModified']
        self.visible_name = metadata['visibleName']
        self.metadata_modified = metadata.get('metadatamodified', False)
        self.modified = metadata.get('modified', False)
        self.synced = metadata.get('synced', False)
        self.version = metadata.get('version')

        if self.type == 'DocumentType':
            self.last_opened = metadata['lastOpened']
            self.last_opened_page = metadata['lastOpenedPage']

    def __setattr__(self, key, value):
        super().__setattr__(key, value)

        if key == 'hash':
            return

        # A dirty translation of the keys to metadata keys
        if key == 'created_time':
            key = 'createdTime'
        if key == 'last_modified':
            key = 'lastModified'
        if key == 'visible_name':
            key = 'visibleName'
        if key == 'metadata_modified':
            key = 'metadatamodified'
        if key == 'last_opened':
            key = 'lastOpened'
        if key == 'last_opened_page':
            key = 'lastOpenedPage'


        self.__metadata[key] = value


class Tag:
    def __init__(self, tag):
        self.name = tag['name']
        self.timestamp = tag['timestamp']

    def to_rm_json(self):
        return {
            'name': self.name,
            'timestamp': self.timestamp
        }

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class DocumentCollection:
    def __init__(self, tags: List[Tag], metadata: Metadata, uuid: str):
        self.tags = tags
        self.metadata = metadata
        self.uuid = uuid

    @property
    def parent(self):
        return self.metadata.parent

    def __repr__(self):
        return f'{self.metadata.visible_name}'


class Document:
    unknown_file_types = set()

    def __init__(self, api: 'API', content: dict, metadata: Metadata, files: List[File], uuid: str):
        self.api = api
        self.content = content
        self.metadata = metadata
        self.files = files
        self.uuid = uuid
        self.files_available = self.check_files_availability()
        self.downloading = False
        pdf_file_uuid = f'{self.uuid}.pdf'
        self.content_files = []
        if self.file_type == 'pdf':
            for file in self.files:
                if file.uuid == pdf_file_uuid:
                    self.content_files.append(file.uuid)
        else:
            if not self.file_type in self.unknown_file_types:
                self.unknown_file_types.add(self.file_type)
                print(f'{Fore.RED}Unknown file type: {self.file_type}{Fore.RESET}')
        self.content_data = {}

    @property
    def file_type(self):
        return self.content['fileType']

    @property
    def available(self):
        return all(file in self.files_available.keys() for file in self.content_files)

    def _download_files(self, callback):
        self.downloading = True
        for file in self.files:
            if file.uuid not in self.content_files:
                continue
            self.content_data[file.uuid] = get_file_contents(self.api, file.hash, binary=True)
        self.downloading = False
        self.files_available = self.check_files_availability()
        callback()

    def _load_files(self):
        for file in self.files:
            if file.uuid not in self.content_files:
                continue
            self.content_data[file.uuid] = get_file_contents(self.api, file.hash, binary=True)

    def ensure_download_and_callback(self, callback):
        if not self.available:
            threading.Thread(target=self._download_files, args=(callback,)).start()
        else:
            if not self.content_data:
                self._load_files()
            callback()

    def check_files_availability(self):
        if not self.api.sync_file_path:
            return {}
        return {file.uuid: file for file in self.files if os.path.exists(os.path.join(self.api.sync_file_path, file.hash))}

    @property
    def parent(self):
        return self.metadata.parent

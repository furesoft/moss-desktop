import os.path
import threading
from typing import List, TYPE_CHECKING, Generic, T, Union, TypedDict

from colorama import Fore

from rm_api.storage.v3 import get_file_contents
from rm_api.templates import BLANK_TEMPLATE

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


class TimestampedValue(Generic[T]):
    def __init__(self, value: dict):
        self.value: T = value['value']
        self.timestamp: str = value['timestamp']

    def create(value: T):
        return TimestampedValue({'value': value, 'timestamp': '0'})


class Page:
    id: str  # This is technically the UUID, a .rm file may or may not exist for this page
    index: TimestampedValue[str]
    template: TimestampedValue[str]
    redirect: Union[TimestampedValue[int], None]

    def __init__(self, page: dict):
        self.__page = page
        self.id = page['id']
        self.index: TimestampedValue[str] = TimestampedValue(page['idx'])
        if template := page.get('template'):
            self.template: TimestampedValue[str] = TimestampedValue(page['template'])
        else:
            self.template = TimestampedValue[str].create(BLANK_TEMPLATE)

        # Check for a redirect
        # If the document is not a notebook this will be on every page
        # Except any user created pages
        if redirect := page.get('redir'):
            self.redirect = TimestampedValue(redirect)
        else:
            self.redirect = None


# TODO: Figure out what the CPagesUUID is refering to
class CPagesUUID(TypedDict):
    first: str
    second: int


class CPages:
    pages: List[Page]
    original: TimestampedValue[int]  # Seems to reference the original page count
    last_opened: TimestampedValue[str]  # The id of the last opened page
    uuids: List[CPagesUUID]

    def __init__(self, c_pages: dict):
        self.__c_pages = c_pages
        self.pages = [Page(page) for page in c_pages['pages']]
        self.original = TimestampedValue(c_pages['original'])
        self.last_opened = TimestampedValue(c_pages['lastOpened'])
        self.uuids = c_pages['uuids']


class Content:
    """
    This class only represents the content data
    of a document and not a document collection.

    EXPLANATION:
        The content of a document collection is much more simple,
        it only contains tags: List[Tag]
        This is handled by the parser and handed to the document collection,
        So this class is only for the content of a document.
    """

    hash: str
    c_pages: Union[CPages, None]
    cover_page_number: int
    file_type: str
    version: int

    def __init__(self, content: dict, content_hash: str):
        self.hash = content_hash
        self.__content = content
        self.c_pages = None
        self.cover_page_number: int = content['coverPageNumber']
        self.dummy_document: bool = content.get('dummyDocument', False)
        self.file_type: str = content['fileType']
        self.version: int = content['formatVersion']

        # Handle the different versions
        if self.version == 2:
            self.parse_version_2()
        else:
            print(f'{Fore.YELLOW}Content file version is unknown: {self.version}{Fore.RESET}')

    def parse_version_2(self):
        self.c_pages = CPages(self.__content['cPages'])

    def parse_version_1(self):
        """
        Version 1 only has pages instead of cPages
        containing a list of uuids
        """
        # TODO: Support content version 1
        pass




class Metadata:
    def __init__(self, metadata: dict, metadata_hash: str):
        self.hash = metadata_hash
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
            self.last_opened_page = metadata.get('lastOpenedPage', 0)

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
    KNOWN_FILE_TYPES = [
        'pdf'
    ]

    def __init__(self, api: 'API', content: Content, metadata: Metadata, files: List[File], uuid: str):
        self.api = api
        self.content = content
        self.metadata = metadata
        self.files = files
        self.uuid = uuid
        self.files_available = self.check_files_availability()
        self.downloading = False

        if self.content.file_type not in self.KNOWN_FILE_TYPES and \
                not self.content.file_type in self.unknown_file_types:
            self.unknown_file_types.add(self.content.file_type)
            print(f'{Fore.RED}Unknown file type: {self.content.file_type}{Fore.RESET}')
        self.content_data = {}

    @property
    def content_files(self):
        return [file.uuid for file in self.files]

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
        return {file.uuid: file for file in self.files if
                os.path.exists(os.path.join(self.api.sync_file_path, file.hash))}

    @property
    def parent(self):
        return self.metadata.parent

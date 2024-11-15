import json
import os.path
import string
import threading
import time
import uuid
from functools import lru_cache
import random
from hashlib import sha256
from sqlite3.dbapi2 import Timestamp
from typing import List, TYPE_CHECKING, Generic, T, Union, TypedDict, Tuple

from colorama import Fore

from rm_api.helpers import get_pdf_page_count
from rm_api.storage.v3 import get_file_contents
from rm_api.templates import BLANK_TEMPLATE

if TYPE_CHECKING:
    from rm_api import API


def now_time():
    return str(int(time.time() * 1000))


def make_uuid():
    return str(uuid.uuid4())


def make_hash(data: Union[str, bytes]):
    if isinstance(data, str):
        return sha256(data.encode()).hexdigest()
    return sha256(data).hexdigest()


class File:
    def __init__(self, file_hash, file_uuid, content_count, file_size, rm_filename=None):
        self.hash = file_hash
        self.uuid = file_uuid
        self.content_count = content_count
        self.size = file_size
        self.rm_filename = rm_filename or file_uuid

    @classmethod
    def from_line(cls, line):
        file_hash, _, file_uuid, content_count, file_size = line.split(':')
        return cls(file_hash, file_uuid, content_count, file_size)

    def to_root_line(self):
        return f'{self.hash}:80000000:{self.uuid}:{self.content_count}:{self.size}\n'

    def to_line(self):
        return f'{self.hash}:0:{self.uuid}:{self.content_count}:{self.size}\n'

    def __repr__(self):
        return f'{self.uuid} ({self.size})[{self.content_count}]'

    def __str__(self):
        return self.__repr__()


class TimestampedValue(Generic[T]):
    def __init__(self, value: dict):
        self.value: T = value['value']
        self.timestamp: str = value['timestamp']

    def to_dict(self):
        return {
            'timestamp': self.timestamp,
            'value': self.value
        }

    @classmethod
    def create(cls, value: T, t1: int = 1, t2: int = 1, bare: bool = False) -> Union[dict, 'TimestampedValue']:
        dictionary = {'timestamp': f'{t1}:{t2}', 'value': value}
        if bare:
            return dictionary
        return cls(dictionary)


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

    @staticmethod
    def new_pdf_redirect_dict(redirection_page: int, index: str, uuid: str = None):
        return {
            "id": uuid if uuid else make_uuid(),
            "idx": {
                "timestamp": "1:2",
                "value": index
            },
            "redir": {
                "timestamp": "1:2",
                "value": redirection_page
            }
        }

    @classmethod
    def new_pdf_redirect(cls, redirection_page: int, index: str, uuid: str = None):
        return cls(cls.new_pdf_redirect_dict(redirection_page, index, uuid))


# TODO: Figure out what the CPagesUUID is referring to
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

    def get_index_from_uuid(self, uuid: str):
        for i, page in enumerate(self.pages):
            if page.id == uuid:
                return i
        return None

    @lru_cache(maxsize=20)
    def get_page_from_uuid(self, uuid: str):
        for page in self.pages:
            if page.id == uuid:
                return page
        return None


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

    def __init__(self, content: dict, content_hash: str, show_debug: bool = False):
        self.hash = content_hash
        self.__content = content
        self.usable = True
        self.c_pages = None
        self.content_file_pdf_check = False
        self.cover_page_number: int = content.get('coverPageNumber', 0)
        self.dummy_document: bool = content.get('dummyDocument', False)
        self.file_type: str = content['fileType']
        self.version: int = content.get('formatVersion')
        self.sizeInBytes: int = content.get('sizeInBytes', -1)
        self.tags: List[Tag] = [Tag(tag) for tag in content.get('tags', ())]

        # Handle the different versions
        if self.version == 2:
            self.parse_version_2()
        elif self.version == 1:
            self.parse_version_1()
        else:
            self.usable = False
            if show_debug:
                if not self.version:
                    print(f'{Fore.RED}Content file version is missing{Fore.RESET}')
                else:
                    print(f'{Fore.YELLOW}Content file version is unknown: {self.version}{Fore.RESET}')

    def parse_version_2(self):
        self.c_pages = CPages(self.__content['cPages'])

    def parse_version_1(self):
        self.version = 2  # promote to version 2
        # Handle error checking since a lot of these can be empty
        try:
            original_page_count = self.__content.pop('originalPageCount')
        except KeyError:
            original_page_count = 0
        try:
            pages = self.__content.pop('pages')
        except KeyError:
            pages = None
        if not pages:
            pages = []
            self.content_file_pdf_check = True
        try:
            redirection_page_map = self.__content.pop('redirectionPageMap')
        except KeyError:
            redirection_page_map = []
        index = self.page_index_generator()
        c_page_pages = []
        last_opened_page = None
        for i, (page, redirection_page) in enumerate(zip(pages, redirection_page_map)):
            c_page_pages.append(Page.new_pdf_redirect_dict(redirection_page, next(index), page))
            if i == self.__content.get('lastOpenedPage'):
                last_opened_page = page

        self.c_pages = CPages(
            {
                'pages': c_page_pages,
                'original': TimestampedValue.create(original_page_count, bare=True),
                'lastOpened': TimestampedValue.create(last_opened_page, bare=True),
                'uuids': {
                    'first': make_uuid(),  # Author
                    'second': 1
                }
            }
        )

    @classmethod
    def new_notebook(cls, author_id: str = None):
        first_page_uuid = make_uuid()
        if not author_id:
            author_id = make_uuid()
        content = {
            'cPages': {
                'lastOpened': TimestampedValue[str].create(first_page_uuid, bare=True),
                'original': TimestampedValue[int].create(-1, 0, 0, bare=True),
                'pages': [{
                    'id': first_page_uuid,
                    'idx': TimestampedValue[str].create('ba', t2=2, bare=True),
                    'template': TimestampedValue[str].create(BLANK_TEMPLATE, bare=True),
                }],
                'uuids': [{
                    'first': author_id,  # This is the author id
                    'second': 1
                }]
            },
            "coverPageNumber": 0,
            "customZoomCenterX": 0,
            "customZoomCenterY": 936,
            "customZoomOrientation": "portrait",
            # rM2 page size
            # TODO: Check values on RPP and if zoom changes
            "customZoomPageHeight": 1872,
            "customZoomPageWidth": 1404,
            "customZoomScale": 1,
            "documentMetadata": {},
            "extraMetadata": {},
            "fileType": "notebook",
            "fontName": "",
            "formatVersion": 2,
            "lineHeight": -1,
            "margins": 125,
            "orientation": "portrait",
            "pageCount": 1,
            "pageTags": [],
            "sizeInBytes": "3289",
            "tags": [],
            "textAlignment": "justify",
            "textScale": 1,
            "zoomMode": "bestFit"
        }
        return cls(content, make_hash(json.dumps(content, indent=4)))

    @classmethod
    def new_pdf(cls):
        content = {
            "dummyDocument": False,
            "extraMetadata": {
                "LastPen": "Finelinerv2",
                "LastTool": "Finelinerv2",
                "ThicknessScale": "",
                "LastFinelinerv2Size": "1"
            },
            "fileType": "pdf",
            "fontName": "",
            "lastOpenedPage": 0,
            "lineHeight": -1,
            "margins": 180,
            "orientation": "portrait",
            "pageCount": 0,
            "pages": [],
            "textScale": 1,
            "transform": {
                "m11": 1,
                "m12": 0,
                "m13": 0,
                "m21": 0,
                "m22": 1,
                "m23": 0,
                "m31": 0,
                "m32": 0,
                "m33": 1
            }
        }

        return cls(content, make_hash(json.dumps(content, indent=4)))

    def to_dict(self) -> dict:
        return self.__content

    def __str__(self):
        return f'content version: {self.version} file type: {self.file_type}'

    @staticmethod
    def page_index_generator():
        # TODO: Figure out the index pattern and make a generator
        while True:
            yield 'ba'

    def check(self, document: 'Document'):
        print(self.content_file_pdf_check, self.file_type)
        if self.content_file_pdf_check and self.file_type == 'pdf':
            self.parse_create_new_pdf_content_file(document)

    def parse_create_new_pdf_content_file(self, document: 'Document'):
        """Creates the c_pages data for a pdf that wasn't indexed"""
        pdf = document.content_data[f'{document.uuid}.pdf']
        page_count = get_pdf_page_count(pdf)

        index = self.page_index_generator()
        self.c_pages.pages = [
            Page.new_pdf_redirect(i, next(index))
            for i in range(page_count)
        ]


class Metadata:
    def __init__(self, metadata: dict, metadata_hash: str):
        self.__metadata = metadata
        self.hash = metadata_hash
        self.type = metadata['type']
        self.parent = metadata['parent'] or None
        self.pinned = metadata['pinned']  # Pinned is equivalent to starred
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

    @classmethod
    def new(cls, name: str, parent: str, document_type: str = 'DocumentType'):
        now = now_time()
        metadata = {
            "deleted": False,
            "lastModified": now,
            "createdTime": now,
            "lastOpened": "",
            "metadatamodified": True,
            "modified": False,
            "parent": parent or '',
            "pinned": False,
            "synced": True,
            "type": document_type,
            "version": 1,
            "visibleName": name
        }
        return cls(metadata, make_hash(json.dumps(metadata, indent=4)))

    def __setattr__(self, key, value):
        super().__setattr__(key, value)

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

        if key not in self.__metadata:
            return

        self.__metadata[key] = value

    def to_dict(self) -> dict:
        return {
            **self.__metadata,
            'parent': self.__metadata['parent'] or ''
        }


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
        self.has_items = False

    @property
    def parent(self):
        return self.metadata.parent

    def __repr__(self):
        return f'{self.metadata.visible_name}'


class Document:
    unknown_file_types = set()
    KNOWN_FILE_TYPES = [
        'pdf', 'notebook'
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
        # TODO: Fix this implementation
        return {file.uuid: file for file in self.files if
                os.path.exists(os.path.join(self.api.sync_file_path, file.hash))}

    def export(self):
        self.content_data[f'{self.uuid}.metadata'] = json.dumps(self.metadata.to_dict(), indent=4).encode()
        self.content_data[f'{self.uuid}.content'] = json.dumps(self.content.to_dict(), indent=4).encode()

    @property
    def parent(self):
        return self.metadata.parent

    @parent.setter
    def parent(self, value):
        self.metadata.parent = value

    def check(self):
        self.content.check(self)

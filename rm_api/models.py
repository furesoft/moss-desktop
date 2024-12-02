import json
import os.path
import string
import threading
import time
import uuid
from copy import copy, deepcopy
from functools import lru_cache
import random
from hashlib import sha256
from io import BytesIO
from sqlite3.dbapi2 import Timestamp
from typing import List, TYPE_CHECKING, Generic, T, Union, TypedDict, Tuple, Dict

from colorama import Fore

from rm_api.helpers import get_pdf_page_count
from rm_api.storage.common import FileHandle
from rm_api.storage.v3 import get_file_contents
from rm_api.templates import BLANK_TEMPLATE
from rm_lines.blocks import write_blocks, blank_document

if TYPE_CHECKING:
    from rm_api import API


def now_time():
    return str(int(time.time() * 1000))


def make_uuid():
    return str(uuid.uuid4())


def make_hash(data: Union[str, bytes, FileHandle]):
    if isinstance(data, FileHandle):
        return data.hash()
    if isinstance(data, str):
        return sha256(data.encode()).hexdigest()
    return sha256(data).hexdigest()


def try_to_load_int(rm_value: str):
    if not rm_value:
        return 0
    else:
        return int(rm_value)


class File:
    def __init__(self, file_hash: str, file_uuid: str, content_count: str, file_size: str, rm_filename=None):
        self.hash = file_hash
        self.uuid = file_uuid
        self.content_count = int(content_count)
        self.size = int(file_size)
        self.rm_filename = rm_filename or file_uuid

    @classmethod
    def from_line(cls, line):
        file_hash, _, file_uuid, content_count, file_size = line.split(':')
        return cls(file_hash, file_uuid, content_count, file_size)

    def to_root_line(self):
        return f'{self.hash}:80000000:{self.uuid}:{self.content_count}:{self.size}\n'

    def to_line(self):
        return f'{self.hash}:0:{self.uuid}:{self.content_count}:{self.size}\n'

    def save_to_cache(self, api: 'API', data: bytes):
        location = os.path.join(api.sync_file_path, self.hash)
        if os.path.exists(location):
            return  # No need cache it if it is already cached
        with open(location, 'wb') as f:
            f.write(data)

    def __repr__(self):
        return f'{self.uuid} ({self.size})[{self.content_count}]'

    def __str__(self):
        return self.__repr__()

    # Parse and re-unparse the file to make a copy
    def __copy__(self):
        return self.from_line(self.to_line())

    def __deepcopy__(self, memo=None):
        return self.from_line(self.to_line())


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

    def to_dict(self):
        result = {
            'id': self.id,
            'idx': self.index.to_dict(),
        }
        if self.template:
            result['template'] = self.template.to_dict()
        if self.redirect:
            result['redir'] = self.redirect.to_dict()

        return result


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

    def to_dict(self) -> dict:
        return {
            'lastOpened': self.last_opened.to_dict(),
            'original': self.original.to_dict(),
            'pages': [page.to_dict() for page in self.pages],
            'uuids': self.uuids
        }


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
    CONTENT_TEMPLATE = {
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
        "formatVersion": 1,
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

    def __init__(self, content: dict, content_hash: str, show_debug: bool = False):
        self.__content = content
        self.hash = content_hash
        self.usable = True
        self.c_pages = None
        self.content_file_pdf_check = False
        self.cover_page_number: int = content.get('coverPageNumber', 0)
        self.dummy_document: bool = content.get('dummyDocument', False)
        self.file_type: str = content['fileType']
        self.version: int = content.get('formatVersion')
        self.size_in_bytes: int = int(content.get('sizeInBytes', '-1'))
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
        return cls(cls.CONTENT_TEMPLATE, make_hash(json.dumps(cls.CONTENT_TEMPLATE, indent=4)))

    def to_dict(self) -> dict:
        return {
            **self.CONTENT_TEMPLATE,
            **self.__content,
            'fileType': self.file_type,
            'formatVersion': self.version,
            'cPages': self.c_pages.to_dict(),
            'tags': [tag.to_rm_json() for tag in self.tags],
            'sizeInBytes': str(self.size_in_bytes),
            'coverPageNumber': self.cover_page_number,
        }

    def __str__(self):
        return f'content version: {self.version} file type: {self.file_type}'

    @staticmethod
    def page_index_generator():
        # TODO: Figure out the index pattern and make a generator
        while True:
            yield 'ba'

    def check(self, document: 'Document'):
        if self.content_file_pdf_check and self.file_type == 'pdf':
            self.parse_create_new_pdf_content_file(document)
            self.content_file_pdf_check = False
        size = 0
        for file in document.files:
            if file.uuid in document.content_data:
                size += len(document.content_data[file.uuid])
        self.size_in_bytes = size

    def _parse_create_new_pdf_content_file(self, pdf: bytes):
        page_count = get_pdf_page_count(pdf)

        index = self.page_index_generator()
        self.c_pages.pages = [
            Page.new_pdf_redirect(i, next(index))
            for i in range(page_count)
        ]

    def parse_create_new_pdf_content_file(self, document: 'Document'):
        """Creates the c_pages data for a pdf that wasn't indexed"""
        pdf = document.content_data[f'{document.uuid}.pdf']

        self._parse_create_new_pdf_content_file(pdf)


class Metadata:
    def __init__(self, metadata: dict, metadata_hash: str):
        self.__metadata = metadata
        self.hash = metadata_hash
        self.type = metadata['type']
        self.parent = metadata['parent'] or None
        self.pinned = metadata['pinned']  # Pinned is equivalent to starred
        self.created_time = try_to_load_int(metadata.get('createdTime'))
        self.last_modified = try_to_load_int(metadata['lastModified'])
        self.visible_name = metadata['visibleName']
        self.metadata_modified = metadata.get('metadatamodified', False)
        self.modified = metadata.get('modified', False)
        self.synced = metadata.get('synced', False)
        self.version = metadata.get('version')

        if self.type == 'DocumentType':
            self.last_opened = try_to_load_int(metadata['lastOpened'])
            self.last_opened_page = metadata.get('lastOpenedPage', 0)

    @classmethod
    def new(cls, name: str, parent: str, document_type: str = 'DocumentType'):
        now = now_time()
        metadata = {
            "deleted": False,
            "lastModified": now,
            "createdTime": now,
            "lastOpened": "",
            "lastOpenedPage": 0,
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
            value = str(value)
        if key == 'last_modified':
            key = 'lastModified'
            value = str(value)
        if key == 'visible_name':
            key = 'visibleName'
        if key == 'metadata_modified':
            key = 'metadatamodified'
        if key == 'last_opened':
            key = 'lastOpened'
            value = str(value)
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
    downloading = False
    available = True

    def __init__(self, tags: List[Tag], metadata: Metadata, uuid: str):
        self.tags = tags
        self.metadata = metadata
        self.uuid = uuid
        self.has_items = False

    @property
    def parent(self):
        return self.metadata.parent

    @property
    def content(self):
        return json.dumps({
            'tags': [tag.to_rm_json() for tag in self.tags]
        })

    @property
    def files(self):
        return [
            File(self.metadata.hash, f'{self.uuid}.metadata', 0, len(self.metadata.to_dict())),
            File(make_hash(self.content), f'{self.uuid}.content', 0, len(self.content)),
        ]

    @property
    def content_data(self):
        return {
            f'{self.uuid}.metadata': json.dumps(self.metadata.to_dict(), indent=4).encode(),
            f'{self.uuid}.content': self.content.encode()
        }

    def __repr__(self):
        return f'{self.metadata.visible_name}'

    @classmethod
    def create(cls, api: 'API', name: str, parent: str = None, document_uuid: str = None):
        if not document_uuid:
            document_uuid = make_uuid()
        return cls([], Metadata.new(name, parent, 'CollectionType'), document_uuid)

    def ensure_download(self):
        pass

    def ensure_download_and_callback(self, callback):
        callback()

    def export(self):
        pass

    def check(self):
        pass

    def check_files_availability(self):
        return {}


class Document:
    unknown_file_types = set()
    KNOWN_FILE_TYPES = [
        'pdf', 'notebook'
    ]
    CONTENT_FILE_TYPES = [
        'pdf', 'rm', 'epub', 'pagedata', '-metadata.json'
    ]

    files: List[File]
    content_data: Dict[str, bytes]

    def __init__(self, api: 'API', content: Content, metadata: Metadata, files: List[File], uuid: str):
        self.api = api
        self.content = content
        self.metadata = metadata
        self.files = files
        self.uuid = uuid
        self.content_data = {}
        self.files_available = self.check_files_availability()
        self.downloading = False
        self.provision = False  # Used during sync to disable opening or exporting the file!!!

        if self.content.file_type not in self.KNOWN_FILE_TYPES and \
                not self.content.file_type in self.unknown_file_types:
            self.unknown_file_types.add(self.content.file_type)
            print(f'{Fore.RED}Unknown file type: {self.content.file_type}{Fore.RESET}')

    @property
    def content_files(self):
        return [file.uuid for file in self.files if
                any(file.uuid.endswith(file_type) for file_type in self.CONTENT_FILE_TYPES)]

    @property
    def file_uuid_map(self):
        return {
            file.uuid: file
            for file in self.files
        }

    @property
    def available(self):
        return all(file in self.files_available.keys() for file in self.content_files)

    # noinspection PyTypeChecker
    def _download_files(self, callback=None):
        self.downloading = True
        for file in self.files:
            if file.uuid not in self.content_files:
                continue
            self.content_data[file.uuid] = get_file_contents(self.api, file.hash, binary=True)
        self.downloading = False
        self.files_available = self.check_files_availability()
        if callback is not None:
            callback()

    def _load_files(self):
        for file in self.files:
            if file.uuid not in self.content_files:
                continue
            if file.uuid in self.content_data:
                continue
            data = get_file_contents(self.api, file.hash, binary=True)
            if data:
                self.content_data[file.uuid] = data

    def unload_files(self):
        to_unload = []
        for file_uuid, data in self.content_data.items():
            if file_uuid in self.content_files:
                to_unload.append(file_uuid)
        for file_uuid in to_unload:
            del self.content_data[file_uuid]

    def load_files_from_cache(self):
        for file in self.files:
            if file.uuid not in self.content_files:
                continue
            data = get_file_contents(self.api, file.hash, binary=True, enforce_cache=True)
            if data:
                self.content_data[file.uuid] = data

    def ensure_download_and_callback(self, callback):
        self.check()
        if not self.available:
            threading.Thread(target=self._download_files, args=(callback,)).start()
        else:
            self._load_files()
            callback()

    def ensure_download(self):
        self.check()
        if not self.available:
            self._download_files()
        else:
            self._load_files()

    def check_files_availability(self):
        if not self.api.sync_file_path:
            return {}
        available = {}
        for file in self.files:
            if file.uuid in self.content_data:  # Check if the file was loaded (could be a new file)
                available[file.uuid] = file
                continue
            if os.path.exists(os.path.join(self.api.sync_file_path, file.hash)):  # Check if the file was cached
                available[file.uuid] = file
                continue
        return available

    def export(self):
        self.content_data[f'{self.uuid}.metadata'] = json.dumps(self.metadata.to_dict(), indent=4).encode()
        self.content_data[f'{self.uuid}.content'] = json.dumps(self.content.to_dict(), indent=4).encode()

        for file in self.files:
            if data := self.content_data.get(file.uuid):
                file.hash = make_hash(data)

    @property
    def parent(self):
        return self.metadata.parent

    @parent.setter
    def parent(self, value):
        self.metadata.parent = value

    def check(self):
        self.content.check(self)

    @classmethod
    def new_notebook(cls, api: 'API', name: str, parent: str = None, document_uuid: str = None) -> 'Document':
        metadata = Metadata.new(name, parent)
        content = Content.new_notebook(api.author_id)
        first_page_uuid = content.c_pages.pages[0].id

        buffer = BytesIO()
        write_blocks(buffer, blank_document(api.author_id))

        if document_uuid is None:
            document_uuid = make_uuid()

        content_data: List[bytes] = [
            json.dumps(content.to_dict(), indent=4).encode(),
            json.dumps(metadata.to_dict(), indent=4).encode(),
            buffer.getvalue()
        ]

        files = [
            File(make_hash(content_data[0]), f"{document_uuid}.content", 0, len(content_data[0])),
            File(make_hash(content_data[1]), f"{document_uuid}.metadata", 0, len(content_data[1])),
            File(make_hash(content_data[2]), f"{document_uuid}/{first_page_uuid}.rm", 0, len(content_data[2])),
        ]

        document = cls(api, content, metadata, files, document_uuid)
        document.content_data = {file.uuid: data for file, data in zip(files, content_data)}
        document.files_available = document.check_files_availability()

        return document

    @classmethod
    def new_pdf(cls, api: 'API', name: str, pdf_data: bytes, parent: str = None, document_uuid: str = None):
        if document_uuid is None:
            document_uuid = make_uuid()
        content = Content.new_pdf()
        metadata = Metadata.new(name, parent)

        content_uuid = f'{document_uuid}.content'
        metadata_uuid = f'{document_uuid}.metadata'
        pdf_uuid = f'{document_uuid}.pdf'

        content_data = {
            content_uuid: json.dumps(content.to_dict(), indent=4),
            metadata_uuid: json.dumps(metadata.to_dict(), indent=4),
            pdf_uuid: pdf_data
        }

        content_hashes = {
            content_uuid: content.hash,
            metadata_uuid: metadata.hash,
            pdf_uuid: make_hash(pdf_data)
        }

        document = cls(api, content, metadata, [
            File(content_hashes[key], key, 0, len(content))
            for key, content in content_data.items()
        ], document_uuid)

        document.content_data = content_data
        document.files_available = document.check_files_availability()

        return document

    @classmethod
    def __copy(cls, document: 'Document', shallow: bool = True):
        # Duplicate content and metadata
        content = Content(document.content.to_dict(), document.file_uuid_map[f'{document.uuid}.content'].hash)
        metadata = Metadata(document.metadata.to_dict(), document.file_uuid_map[f'{document.uuid}.metadata'].hash)

        # Make a new document
        if shallow:
            files = document.files
        else:
            files = [
                copy(file)
                for file in document.files
            ]

        new = cls(document.api, content, metadata, files, document.uuid)
        if shallow:
            new.content_data = copy(document.content_data)
        else:
            new.content_data = deepcopy(document.content_data)
        new.files_available = new.check_files_availability()
        return new

    def __copy__(self):
        return self.__copy(self)

    def __deepcopy__(self, memo=None):
        return self.__copy(self, shallow=False)

    def replace_pdf(self, pdf_data: bytes):
        pdf_uuid = f'{self.uuid}.pdf'
        document = deepcopy(self)

        pdf_file_info = document.file_uuid_map[pdf_uuid]

        pdf_file_info.hash = make_hash(pdf_data)
        pdf_file_info.content_count = len(pdf_data)

        document.content_data[pdf_uuid] = pdf_data

        document.files_available = document.check_files_availability()

        return document

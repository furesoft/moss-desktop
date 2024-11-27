import json
import os.path
import shutil
import zipfile
from functools import wraps, lru_cache
from io import BytesIO
from threading import Thread
from typing import Any, Callable

import pygameextra as pe
import re

from PIL import Image
from requests import Session

from gui.cloud_action_helper import surfaces_to_pdf
from gui.defaults import Defaults
from gui.preview_handler import PreviewHandler
from gui.screens.name_field_screen import NameFieldScreen
from melora.callback_document import CallbackDocument
from melora.extension_base import ExtensionBase
from rm_api import Document, FileSyncProgress
from rm_api.models import Page

SITE_URL = 'https://imhentai.xxx'
PROFILE_URL = f'{SITE_URL}/profile/'
FAVORITES_URL = f'{SITE_URL}/user/fav_pags.php'
DOWNLOAD_REQUEST_URL = f'{SITE_URL}/inc/dl_new.php'
DOWNLOAD_REQUEST_PAGES = f'{SITE_URL}/downloads/{{}}/{{}}.js'
DOWNLOAD_PAGE = 'https://m{}.imhentai.xxx/{}/{}/{}'
GALLERY_URL = f'{SITE_URL}/gallery/{{}}'


def threaded(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs, daemon=True)
        thread.start()
        return thread

    return wrapper


def wrap_callback(fn, *args, **kwargs):
    return lambda: fn(*args, **kwargs)


def extract_galleries(response_text):
    pattern = r'/gallery/\d+/'
    galleries = set(re.findall(pattern, response_text))
    return tuple(f'{SITE_URL}{gallery}' for gallery in galleries)


def extract_gallery_info(response_text):
    cover_pattern = r'https://.*?cover\.jpg'
    ids_to_extract = ['gallery_title', 'load_id', 'load_dir', 'gallery_id', 'load_server']
    extracted_info = {}

    for input_id in ids_to_extract:
        pattern = rf'<input[^>]*id="{input_id}"[^>]*value="([^"]+)"[^>]*>'
        match = re.search(pattern, response_text)
        extracted_info[input_id] = match.group(1) if match else None

    cover_match = re.search(cover_pattern, response_text)
    cover_url = cover_match.group(0) if cover_match else None

    return {
        'download_info': extracted_info,
        'cover_url': cover_url
    }


def filter_and_sort_images(files):
    def is_image(file):
        return re.fullmatch(r'\d+\.\w+', file)

    return sorted(filter(is_image, files), key=lambda x: int(x.split('.')[0]))


class Extension(ExtensionBase):
    ID = 'imhentai_gallery_downloader'
    NAME = "ImHentai Gallery Downloader"
    SHORT = 'ImHentai'
    AUTHOR = "Manga Extensions"
    ACTIONS = {
        "Download Gallery": "download_gallery"
    }

    def __init__(self, injector):
        super().__init__(injector)
        self.path_to_config = os.path.join(Defaults.MELORA_CONFIG_DIR, 'imhentai_gallery_downloader.json')
        self.path_to_zip = os.path.join(Defaults.MELORA_CONFIG_DIR, 'temp.zip')
        self.path_to_extract = os.path.join(Defaults.MELORA_CONFIG_DIR, 'zip_extract')
        self.config = {}
        self.session = Session()
        self.temp_collection = None

    def load(self):
        if os.path.exists(self.path_to_config):
            with open(self.path_to_config, 'r') as f:
                self.config = json.load(f)
        else:
            self.save()

    def save(self):
        self.discard_temp_collection()
        with open(self.path_to_config, 'w') as f:
            json.dump(self.config, f)

    def discard_temp_collection(self):
        if self.temp_collection:
            parent = self.api.document_collections[self.temp_collection].parent
            documents_to_delete = [uuid for uuid, document in self.api.documents.items() if
                                   document.parent == self.temp_collection]
            for document_uuid in documents_to_delete:
                del self.api.documents[document_uuid]
            del self.api.document_collections[self.temp_collection]
            self.temp_collection = None
            self.gui.main_menu.set_parent(parent)

    def authenticate(self):
        token = self.config.get('token')

        if not token:
            NameFieldScreen(self.gui, f"{self.SHORT} PHPSESSID", on_submit=self.set_session_id)
            return False

        self.session.cookies['PHPSESSID'] = token

        if not self.check_auth():
            del self.config['token']
            return self.authenticate()

        return True

    def check_auth(self):
        response = self.session.get(PROFILE_URL, allow_redirects=False)
        return response.status_code == 200

    def set_session_id(self, token: str):
        self.config['token'] = token

    def get_gallery_info(self, url: str):
        response = self.session.get(url)

        return {
            **extract_gallery_info(response.text)
        }

    @staticmethod
    def get_referer_headers(url):
        return {
            'Referer': url,
            'X-Requested-With': 'XMLHttpRequest'
        }

    @lru_cache
    def get_favorites(self):
        response = self.session.get(FAVORITES_URL, headers=self.get_referer_headers(PROFILE_URL))
        galleries = extract_galleries(response.text)
        infos = [self.get_gallery_info(gallery) for gallery in galleries]
        return infos

    def load_url_image(self, url):
        pil_image = Image.open(self.session.get(url, stream=True).raw)
        return pe.Image(
            pe.pygame.image.frombytes(pil_image.tobytes(), pil_image.size, 'RGB').convert()
        )

    def get_download_url(self, download_info):
        response = self.session.post(
            DOWNLOAD_REQUEST_URL,
            data=download_info,
            headers=self.get_referer_headers(GALLERY_URL.format(download_info['gallery_id']))
        )

        status, url = response.text.split(',', 1)
        if status == 'success':
            return url
        return None

    def get_download_pages(self, download_info):
        response = self.session.post(
            DOWNLOAD_REQUEST_PAGES.format(download_info['load_dir'], download_info['load_id']),
            data=download_info,
            headers=self.get_referer_headers(GALLERY_URL.format(download_info['gallery_id']))
        )

        page_info = json.loads(response.text.strip().split('=')[1])
        pages = {}
        for page in page_info:
            item = page['item']
            item_name = item.split('|')[0]
            pages[item_name] = DOWNLOAD_PAGE.format(
                download_info['load_server'],
                download_info['load_dir'],
                download_info['load_id'],
                item_name
            )

        return pages

    @threaded
    def download(self, gallery_info):
        # Get the download url
        download_url = self.get_download_url(gallery_info['download_info'])

        if not download_url:
            return
        self.discard_temp_collection()
        self.gui.import_screen.predefine_item()

        check_ok = self.session.head(download_url, stream=True)

        if os.path.exists(self.path_to_extract):
            shutil.rmtree(self.path_to_extract)
        os.makedirs(self.path_to_extract)

        if check_ok.ok:
            # Download the zip file
            response = self.session.get(download_url, stream=True)
            if os.path.exists(self.path_to_zip):
                os.remove(self.path_to_zip)
            with open(self.path_to_zip, 'wb') as f:
                for chunk in response.iter_content(chunk_size=int(3e6)):
                    f.write(chunk)

            # Extract the zip file
            with zipfile.ZipFile(self.path_to_zip, 'r') as zip_ref:
                zip_ref.extractall(self.path_to_extract)
        else:
            pages = self.get_download_pages(gallery_info['download_info'])
            for page_filename, page_url in pages.items():
                path = os.path.join(self.path_to_extract, page_filename)
                response = self.session.get(page_url, stream=True)
                with open(path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=int(3e6)):
                        f.write(chunk)

        # Find all the enumerated images
        images = []

        for file in filter_and_sort_images(os.listdir(self.path_to_extract)):
            path = os.path.join(self.path_to_extract, file)
            images.append(pe.Image(path).surface)

        pdf = surfaces_to_pdf(images)
        document = Document.new_pdf(
            self.api, gallery_info['download_info']['gallery_title'],
            pdf, self.gui.main_menu.navigation_parent
        )
        self.gui.import_screen.add_item(document)

    @threaded
    def download_gallery(self):
        if not self.authenticate():
            return
        self.discard_temp_collection()
        self.temp_collection = self.injector.create_temp_collection(f'{self.SHORT} Favorites')
        load_progress = FileSyncProgress()
        load_progress.total = 1

        self.api.spread_event(load_progress)

        favorites = self.get_favorites()
        load_progress.total = len(favorites)

        for favorite in favorites:
            preview = PreviewHandler.CACHED_PREVIEW.get(favorite['download_info']['gallery_id'])
            if not preview or not preview[1]:
                preview = self.load_url_image(favorite['cover_url'])
                PreviewHandler.CACHED_PREVIEW[favorite['download_info']['gallery_id']] = ('0', preview)
            else:
                preview = preview[1]
            pdf = surfaces_to_pdf([preview.surface])
            document = CallbackDocument.new_pdf(
                self.api, favorite['download_info']['gallery_title'],
                pdf, self.temp_collection, document_uuid=favorite['download_info']['gallery_id']
            )

            document.check()
            document.content.c_pages.pages[0].id = '0'
            document.maintain_preview = PreviewHandler.CACHED_PREVIEW[favorite['download_info']['gallery_id']]

            document.callback = wrap_callback(self.download, favorite)

            self.api.documents[document.uuid] = document
            load_progress.done += 1

        load_progress.finished = True

        self.gui.main_menu.get_items()

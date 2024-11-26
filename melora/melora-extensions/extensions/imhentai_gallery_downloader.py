import json
import os.path
from functools import wraps
from threading import Thread
import re

from requests import Session

from gui.defaults import Defaults
from gui.screens.name_field_screen import NameFieldScreen
from melora.extension_base import ExtensionBase

SITE_URL = 'https://imhentai.xxx'
PROFILE_URL = f'{SITE_URL}/profile/'
FAVORITES_URL = f'{SITE_URL}/user/fav_pags.php'


def threaded(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs, daemon=True)
        thread.start()
        return thread

    return wrapper


def extract_galleries(response_text):
    pattern = r'/gallery/\d+/'
    galleries = set(re.findall(pattern, response_text))
    return tuple(f'{SITE_URL}{gallery}' for gallery in galleries)


def extract_gallery_info(response_text):
    cover_pattern = r'https://.*?cover\.jpg'
    ids_to_extract = ['gallery_title', 'load_id', 'load_dir', 'gallery_id']
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


class Extension(ExtensionBase):
    ID = 'imhentai_gallery_downloader'
    NAME = "ImHentai Gallery Downloader"
    SHORT = 'ImHentai'
    ACTIONS = {
        "Download Gallery": "download_gallery"
    }

    def __init__(self, injector):
        super().__init__(injector)
        self.path_to_config = os.path.join(Defaults.MELORA_CONFIG_DIR, '', 'imhentai_gallery_downloader.json')
        self.config = {}
        self.session = Session()

    def load(self):
        if os.path.exists(self.path_to_config):
            with open(self.path_to_config, 'r') as f:
                self.config = json.load(f)
        else:
            self.save()

    def save(self):
        with open(self.path_to_config, 'w') as f:
            json.dump(self.config, f)

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

    def get_favorites(self):
        response = self.session.get(FAVORITES_URL, headers=self.get_referer_headers(PROFILE_URL))
        galleries = extract_galleries(response.text)
        infos = [self.get_gallery_info(gallery) for gallery in galleries]
        print(infos)

    @threaded
    def download_gallery(self):
        if not self.authenticate():
            return
        temp_collection = self.injector.create_temp_collection(f'{self.SHORT} Favorites')
        favorites = self.get_favorites()

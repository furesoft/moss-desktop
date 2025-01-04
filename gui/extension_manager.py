import json
import os.path
import time

from extism import Plugin
from extism import Error as ExtismError
from io import StringIO
from typing import TYPE_CHECKING

from colorama import Fore
from requests.hooks import HOOKS

from gui.defaults import Defaults

if TYPE_CHECKING:
    from gui import GUI


def output_to_dict(func):
    def wrapper(self, output, *args, **kwargs):
        return func(self, json.loads(bytes(output).decode()), *args, **kwargs)

    return wrapper


class ExtensionManager:
    extensions_to_load: list
    extra_items: dict
    extension_count: int
    extensions_loaded: int
    extensions: dict
    extension_load_log: StringIO

    HOOK = 'em_extension_hook'

    def __init__(self, gui: 'GUI'):
        self.gui = gui
        self._reset()
        self.gui.api.add_hook(self.HOOK, self.handle_hook)

    def reset(self):
        for extension in self.extensions.values():
            try:
                extension.call('unregister', b'')
            except ExtismError:
                self.error(f"Extension {extension} failed to unregister")
        self.gui.api.remove_hook(self.HOOK)
        self._reset()

    def _reset(self):
        self.extensions_to_load = []
        self.extra_items = {}
        self.extension_count = 0
        self.extensions_loaded = 0
        self.extensions = {}
        self.extension_load_log = StringIO()

    def log(self, message: str):
        self.write(f'LOG {message}\n')

    def error(self, message: str):
        self.write(f'ERROR {message}\n')

    def write(self, message: str):
        self.extension_load_log.write(message)
        self.gui.api.log(message[:-1], enable_print=False)
        if self.gui.config.debug:
            print(
                "DEBUG EM:",
                f"""{
                Fore.LIGHTBLACK_EX if message.startswith('LOG') else
                Fore.RED if message.startswith('ERROR') else
                ''
                }"""
                f"{message}"
                f"{Fore.RESET}",
                end=''
            )

    def load_wasm(self, extension_path: str, extension_name: str):
        if not os.path.exists(extension_path):
            self.error(f"Extension {extension_path} file not found")
            self.extension_count -= 1
            return
        with open(extension_path, 'rb') as f:
            data = f.read()
        self.load_wasm_source(data, extension_name)

    def load_wasm_source(self, source: bytes, extension_name: str):
        extension = Plugin(source)
        try:
            extension.call('register', b'',
                           lambda output: self.handle_register_output(output, extension_name))
            self.log(f"Registered extension {extension}")
        except ExtismError:
            self.extension_count -= 1
            self.error(f"Extension {extension_name} failed to register")
            return
        self.extensions[extension_name] = extension
        self.extensions_loaded += 1

    def gather_extensions(self):
        for extension in os.listdir(Defaults.EXTENSIONS_DIR):
            self.extensions_to_load.append(extension)

    def load(self):
        self.reset()
        self.gather_extensions()
        self._load()

    def _load(self):
        self.extension_count = len(self.extensions_to_load)
        for extension in self.extensions_to_load:
            self.log(f"Loading extension {extension}")
            if self.gui.config['extensions'].get(extension) is None:
                self.gui.config['extensions'][extension] = False
                self.gui.dirty_config = True
            if self.gui.config['extensions'][extension]:
                self.load_wasm(os.path.join(Defaults.EXTENSIONS_DIR, extension, f'{extension}.wasm'), extension)
            else:
                self.extension_count -= 1
                self.error(f"Extension {extension} is disabled, enable it in the config!")

    @output_to_dict
    def handle_register_output(self, output: dict, extension_name: str):
        for file in output['files']:
            self.extra_items[file['key']] = os.path.join(Defaults.EXTENSIONS_DIR, extension_name, file['path'])

    def handle_hook(self, event):
        ...
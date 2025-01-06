import json
import os.path
from traceback import print_exc

import extism
from extism import Plugin
from extism import Error as ExtismError
from io import StringIO
from typing import TYPE_CHECKING, Dict

from .host_functions import init_host_functions
from colorama import Fore

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
    extensions: Dict[str, Plugin]
    extension_load_log: StringIO
    context_menus: dict

    HOOK = 'em_extension_hook'

    def __init__(self, gui: 'GUI'):
        self.gui = gui
        self._reset()
        self.gui.api.add_hook(self.HOOK, self.handle_hook)
        self.opened_context_menus = []
        self._current_extension = None
        init_host_functions(self)
        extism.set_log_file('extism.log', 'error')

    def reset(self):
        for extension_name, extension in self.extensions.items():
            self.current_extension = extension_name
            try:
                extension.call('unregister', b'')
            except ExtismError:
                self.error(f"Extension {extension} failed to unregister")
                print_exc()
            del extension
        self.gui.api.remove_hook(self.HOOK)
        self._reset()

    def _reset(self):
        self.extensions_to_load = []
        self.extra_items = {}
        self.extension_count = 0
        self.extensions_loaded = 0
        self.extensions = {}
        self.context_menus = {}
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
        extension = Plugin(source, True)
        try:
            self.extensions[extension_name] = extension
            self.current_extension = extension_name
            extension.call('register', b'',
                           lambda output: self.handle_register_output(output, extension_name))
            self.log(f"Registered extension {extension_name}")
        except ExtismError:
            self.extensions.pop(extension_name)
            self.extension_count -= 1
            self.error(f"Extension {extension_name} failed to register")
            print_exc()
            return
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
                try:
                    self.load_wasm(os.path.join(Defaults.EXTENSIONS_DIR, extension, f'{extension}.wasm'), extension)
                except ExtismError:
                    self.error(f"Extension {extension} failed to load")
                    self.extension_count -= 1
                    print_exc()
            else:
                self.extension_count -= 1
                self.error(f"Extension {extension} is disabled, enable it in the config!")

    @output_to_dict
    def handle_register_output(self, output: dict, extension_name: str):
        for file in output['files']:
            self.extra_items[file['key']] = os.path.join(Defaults.EXTENSIONS_DIR, extension_name, file['path'])

    def handle_hook(self, event):
        ...

    def loop(self):
        state = {
            'width': self.gui.width,
            'height': self.gui.height,
            'current_screen': self.gui.screens.queue[-1].__class__.__name__ if self.gui.screens.queue else "",
            'opened_context_menus': self.opened_context_menus
        }
        for extension_name, extension in self.extensions.items():
            self.current_extension = extension_name
            try:
                extension.call('extension_loop', json.dumps(state).encode())
            except ExtismError:
                self.error(f"Extension {extension} failed to loop")
                print_exc()
        self.opened_context_menus.clear()

    @property
    def current_extension(self):
        return self._current_extension

    @current_extension.setter
    def current_extension(self, extension_key: str):
        self._current_extension = extension_key

    @property
    def current_extism(self):
        if not self.current_extension:
            return None
        return self.extensions[self.current_extension]
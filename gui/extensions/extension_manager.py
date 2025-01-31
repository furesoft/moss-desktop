import json
import os.path
from functools import lru_cache
from io import StringIO
from json import JSONDecodeError
from traceback import print_exc
from typing import TYPE_CHECKING, Dict, List

import extism
from colorama import Fore
from extism import Error as ExtismError
from extism import Plugin
from extism.extism import HOST_FN_REGISTRY

from gui.defaults import Defaults
from .host_functions import init_host_functions
from .input_types import TContextButton

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
    metadata_objects: dict
    content_objects: dict
    extension_buttons: List[TContextButton]

    HOOK = 'em_extension_hook'

    def __init__(self, gui: 'GUI'):
        self.gui = gui
        self.opened_context_menus = []
        self.dirty_configs = []
        self.extensions_to_load = []
        self.loaded_extensions = []
        self.extension_buttons: List[TContextButton] = []
        self.extra_items = {}
        self.extensions = {}
        self.context_menus = {}
        self.metadata_objects = {}
        self.content_objects = {}
        self.texts = {}
        self.screens = {}
        self.configs = {}
        self._reset()
        self._current_extension = None
        self.gathered_extensions = False
        init_host_functions(self)
        extism.set_log_file('extism.log', 'info')
        self.init()

    def init(self):
        self.gui.api.add_hook(self.HOOK, self.handle_hook)

    def reset(self):
        for extension_name, extension in self.extensions.items():
            self.current_extension = extension_name
            try:
                extension.call('moss_extension_unregister', b'')
            except ExtismError:
                self.error(f"Extension {extension} failed to unregister")
                print_exc()
            del extension
        self.gui.api.remove_hook(self.HOOK)
        self.extension_load_log.close()
        self._reset()

    def _reset(self):
        self.extensions_to_load.clear()
        self.loaded_extensions.clear()
        self.extension_buttons.clear()
        self.extra_items.clear()
        self.extensions.clear()
        self.context_menus.clear()
        self.metadata_objects.clear()
        self.content_objects.clear()
        self.texts.clear()
        self.screens.clear()
        self.configs.clear()
        self.extension_count = 0
        self.extensions_loaded = 0
        self.extension_load_log = StringIO()

    def log(self, message: str):
        self.write(f'LOG {message}\n')

    def error(self, message: str):
        self.write(f'ERROR {message}\n')

    def warn(self, message: str):
        self.write(f'WARN {message}\n')

    def write(self, message: str):
        self.extension_load_log.write(message)
        self.gui.api.log(message[:-1], enable_print=False)
        if self.gui.config.debug:
            print(
                "DEBUG EM:",
                f"""{
                Fore.LIGHTBLACK_EX if message.startswith('LOG') else
                Fore.RED if message.startswith('ERROR') else
                Fore.YELLOW if message.startswith('WARN') else
                ''
                }"""
                f"{message}"
                f"{Fore.RESET}",
                end=''
            )

    def load_wasm(self, extension_path: str, config_path: str, extension_name: str):
        if not os.path.exists(extension_path):
            self.error(f"Extension {extension_path} file not found")
            self.extension_count -= 1
            return
        if not os.path.exists(config_path):
            self.configs[extension_name] = {}
            self.dirty_configs = [extension_name]
        else:
            try:
                with open(config_path, 'r') as f:
                    self.configs[extension_name] = json.load(f)
            except JSONDecodeError:
                self.warn(f"Extension {extension_path} config could not be parsed. Resetting!")
                self.configs[extension_name] = {}
            except UnicodeDecodeError:
                self.warn(f"Extension {extension_path} config could not be read. Resetting!")
                self.configs[extension_name] = {}

        with open(extension_path, 'rb') as f:
            data = f.read()
        self.load_wasm_source(data, extension_name)

    def load_wasm_source(self, source: bytes, extension_name: str):
        extension = Plugin(source, True, functions=[
            fn for fn in HOST_FN_REGISTRY if getattr(fn, 'moss', False)
        ])
        self.extensions[extension_name] = extension
        self.current_extension = extension_name
        if extension.function_exists('_start'):
            try:
                extension.call('_start', b'')
            except ExtismError:
                self.error(f"Extension {extension_name} failed to start")
                print_exc()
                return
        try:
            extension.call('moss_extension_register', self.state,
                           lambda output: self.handle_register_output(output, extension_name))
        except ExtismError:
            self.extensions.pop(extension_name)
            self.extension_count -= 1
            self.error(f"Extension {extension_name} failed to register")
            print_exc()
            return
        self.log(f"Registered extension {extension_name}")
        self.loaded_extensions.append(extension_name)
        self.extensions_loaded += 1

    def gather_extensions(self):
        for extension in os.listdir(Defaults.EXTENSIONS_DIR):
            if extension.startswith('_'):
                continue
            if extension.endswith('.wasm'):
                extension_name = extension[:-5]
                os.makedirs(os.path.join(Defaults.EXTENSIONS_DIR, extension_name), exist_ok=True)
                os.rename(
                    os.path.join(Defaults.EXTENSIONS_DIR, extension),
                    os.path.join(Defaults.EXTENSIONS_DIR, extension_name, extension)
                )
                self.extensions_to_load.append(extension_name)
                continue
            if os.path.isfile(os.path.join(Defaults.EXTENSIONS_DIR, extension)):
                continue
            self.extensions_to_load.append(extension)
        self.gathered_extensions = True

    def load(self, loader):
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
            wasm_file_location = os.path.join(Defaults.EXTENSIONS_DIR, extension, f'{extension}.wasm')
            info_file_location = os.path.join(Defaults.EXTENSIONS_DIR, extension, f'{extension}.info')
            if os.path.exists(info_file_location):
                with open(info_file_location, 'r') as f:
                    info = json.load(f)
                if file_location := info.get('file'):
                    wasm_file_location = os.path.join(Defaults.EXTENSIONS_DIR, extension, file_location)
                    if not wasm_file_location.startswith(os.path.join(Defaults.EXTENSIONS_DIR, extension)):
                        self.error(f"Extension {extension} file location is invalid or dangerous")
                        self.extension_count -= 1
                        continue

            if not os.path.exists(wasm_file_location):
                self.error(f"Extension {extension} file not found")
                self.extension_count -= 1
                continue

            if self.gui.config['extensions'][extension]:
                try:
                    self.load_wasm(
                        wasm_file_location,
                        os.path.join(Defaults.OPTIONS_DIR, f'{extension}.json'),
                        extension
                    )
                except ExtismError:
                    self.error(f"Extension {extension} failed to load.")
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
        if self.extra_items or len(self.loaded_extensions) < self.extension_count:
            return
        for extension_name, extension in self.extensions.items():
            if extension_name not in self.loaded_extensions:
                continue
            self.current_extension = extension_name
            try:
                extension.call(
                    'moss_extension_loop',
                    self.state
                )
            except ExtismError:
                self.error(f"Extension {extension} failed to loop")
                print_exc()
        self.opened_context_menus.clear()

    @lru_cache
    def action(self, action: str, extension_name: str):
        def _action(**kwargs):
            self.current_extension = extension_name
            try:
                self.extensions[extension_name].call(action, json.dumps(kwargs).encode() if kwargs else b'')
            except ExtismError:
                self.error(f"Extension {extension_name} failed to handle action {action}")
                print_exc()

        return _action

    @property
    def raw_state(self):
        return {
            'width': self.gui.width,
            'height': self.gui.height,
            'current_screen': self.gui.screens.queue[-1].__class__.__name__ if self.gui.screens.queue else "",
            'opened_context_menus': self.opened_context_menus,
            'icons': list(self.gui.icons.keys()),
        }

    @property
    def state(self):
        return json.dumps(self.raw_state).encode()

    def save_configs(self):
        for config, config_path in map(
                lambda extension_name: (
                        self.configs[extension_name],
                        os.path.join(
                            Defaults.OPTIONS_DIR,
                            f'{extension_name}.json'
                        )),
                self.dirty_configs
        ):
            if not config:
                continue
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)

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

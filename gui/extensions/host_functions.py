from functools import wraps
from typing import TYPE_CHECKING, Annotated, Type, Any

from box import Box
from extism import host_fn, Json

from .input_types import TContextMenu
from ..pp_helpers import ContextMenu

if TYPE_CHECKING:
    from gui import GUI
    from rm_api import API
    from .extension_manager import ExtensionManager

extension_manager: 'ExtensionManager'
gui: 'GUI'
api: 'API'


def init_host_functions(_extension_manager: 'ExtensionManager'):
    global gui, api, extension_manager
    extension_manager = _extension_manager
    gui = _extension_manager.gui
    api = gui.api


def transform_to_json(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs) -> Annotated[dict, Json]:
        return {
            'value': fn(*args, **kwargs)
        }

    return wrapper


def unpack(fn):
    fn.__annotations__ = {'value': Annotated[dict, Json]}
    fn.__name__ = f'_{fn.__name__}'

    @wraps(fn)
    def wrapper(value: Annotated[dict, Json]):
        return fn(**value)

    return wrapper


@host_fn()
def moss_gui_register_context_menu(menu: Annotated[TContextMenu, Json]):
    context_menu = Box(menu)

    class CustomContextMenu(ContextMenu):
        KEY = context_menu.key
        BUTTONS = tuple(
            {
                key:
                    value if value else None
                for key, value in button.items()
                if value or key == "action" and not value
            }
            for button in context_menu.buttons
        )

    extension_manager.log(f"Registered context menu {extension_manager.current_extension}.{context_menu.key}")

    extension_manager.context_menus[context_menu.key] = CustomContextMenu


@host_fn()
def moss_gui_open_context_menu(key: str, x: int, y: int):
    context_menu_class: Type[ContextMenu] = extension_manager.context_menus[key]
    context_menu = context_menu_class(gui.main_menu, (x, y))
    gui.main_menu.context_menus[key] = context_menu


@host_fn()
@transform_to_json
def moss_em_config_get(key: str) -> Annotated[str, Json]:
    return extension_manager.configs[extension_manager.current_extension].get(key)


@host_fn()
@unpack
def moss_em_config_set(key: str, value: Any):
    extension_manager.configs[extension_manager.current_extension][key] = value
    if extension_manager.current_extension not in extension_manager.dirty_configs:
        extension_manager.dirty_configs.append(extension_manager.current_extension)

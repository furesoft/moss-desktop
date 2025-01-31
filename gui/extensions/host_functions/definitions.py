import inspect
from functools import wraps
from typing import TYPE_CHECKING, Annotated, Optional, Tuple, Union, List, get_origin

import pygameextra as pe
from colorama import Fore
from extism import host_fn as extism_host_fn, Json, ValType
from extism.extism import HOST_FN_REGISTRY

from ..export_types import TValue
from ..input_types import color_from_tuple, color_to_tuple, TTextColors, TColor, text_colors_to_tuple

if TYPE_CHECKING:
    from gui import GUI
    from rm_api import API
    from ..extension_manager import ExtensionManager

extension_manager: 'ExtensionManager'
gui: 'GUI'
api: 'API'
ACTION_APPEND = '__em_action_'


def init_host_functions(_extension_manager: 'ExtensionManager'):
    global gui, api, extension_manager
    extension_manager = _extension_manager
    gui = _extension_manager.gui
    api = gui.api


def transform_to_json(fn):
    fn.__annotations__['return'] = Annotated[TValue, Json]

    @wraps(fn)
    def wrapper(*args, **kwargs) -> Annotated[TValue, Json]:
        return {
            'value': fn(*args, **kwargs)
        }

    return wrapper


def host_fn(
        name: Optional[str] = None,
        namespace: Optional[str] = None,
        signature: Optional[Tuple[List[ValType], List[ValType]]] = None,
        user_data: Optional[Union[bytes, List[bytes]]] = None,
):
    extism_wrapper = extism_host_fn(name, namespace, signature, user_data)

    @wraps(extism_wrapper)
    def wrapped_extism(fn):
        if pe.settings.config.debug_log:
            sig = inspect.signature(fn)
            params = ", ".join(
                str(param.annotation.__args__[0] if get_origin(param.annotation) is Annotated else param)
                for param in sig.parameters.values()
            )
            return_annotation = (sig.return_annotation.__args__[0]
                                 if get_origin(sig.return_annotation) is Annotated else sig.return_annotation) \
                if sig.return_annotation is not sig.empty else None
            return_type = f" -> {return_annotation.__name__}" if return_annotation else ""
            print(f'HOST FUNCTION - {name or fn.__name__}({params}){return_type}')
        return extism_wrapper(fn)

    @wraps(wrapped_extism)
    def wrapper(fn):
        result = wrapped_extism(fn)
        setattr(HOST_FN_REGISTRY[-1], 'moss', True)

        return result

    return wrapper


def unpack(fn):
    fn.__annotations__.pop('key')
    fn.__annotations__['value'] = Annotated[dict, Json]
    fn.__name__ = f'_{fn.__name__}'

    @wraps(fn)
    def wrapper(*args, **kwargs):
        value, *args = args
        print(f'fn({args}, {({**value, **kwargs})})')
        return fn(*args, **value, **kwargs)

    return wrapper


def debug_result(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        result = fn(*args, **kwargs)
        print(f'{Fore.CYAN}HOST FUNCTION{Fore.RESET} - {fn.__name__} result: {result}')
        return result

    return wrapper


def set_color(fn):
    fn.__annotations__ = {'key': str, 'color': Annotated[TColor, Json]}

    @wraps(fn)
    def wrapper(key: str, color: Annotated[TColor, Json]):
        return fn(key, color_to_tuple(color))

    return wrapper


def get_color(fn):
    fn.__annotations__ = {'key': str, 'return': Annotated[TColor, Json]}

    @wraps(fn)
    def wrapper(key: str):
        color = fn(key)
        return color_from_tuple(color)

    return wrapper


def get_text_color(fn):
    fn.__annotations__ = {'key': str, 'return': Annotated[TTextColors, Json]}

    @wraps(fn)
    def wrapper(key: str):
        colors = fn(key)
        return {
            'foreground': color_from_tuple(colors[0]),
            'background': color_from_tuple(colors[1], allow_turn_to_none=True)
        }

    return wrapper


def set_text_color(fn):
    fn.__annotations__ = {
        'key': str,
        'colors': Annotated[TTextColors, Json]
    }

    @wraps(fn)
    def wrapper(key: str, colors: Annotated[TTextColors, Json]):
        return fn(key, text_colors_to_tuple(colors))

    return wrapper

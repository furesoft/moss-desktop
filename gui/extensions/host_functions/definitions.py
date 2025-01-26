from functools import wraps
from typing import TYPE_CHECKING, Annotated, Optional, Tuple, Union, List

from extism import host_fn as extism_host_fn, Json, ValType
from extism.extism import HOST_FN_REGISTRY

from ..input_types import color_from_tuple, color_to_tuple, TTextColor, TColor

if TYPE_CHECKING:
    from gui import GUI
    from rm_api import API
    from ..extension_manager import ExtensionManager

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


def host_fn(
        name: Optional[str] = None,
        namespace: Optional[str] = None,
        signature: Optional[Tuple[List[ValType], List[ValType]]] = None,
        user_data: Optional[Union[bytes, List[bytes]]] = None,
):
    func = extism_host_fn(name, namespace, signature, user_data)

    @wraps(func)
    def wrapper(fn):
        result = func(fn)
        setattr(HOST_FN_REGISTRY[-1], 'moss', True)

        return result

    return wrapper


def unpack(fn):
    fn.__annotations__ = {'value': Annotated[dict, Json]}
    fn.__name__ = f'_{fn.__name__}'

    @wraps(fn)
    def wrapper(value: Annotated[dict, Json]):
        return fn(**value)

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
    fn.__annotations__ = {'key': str, 'return': Annotated[TTextColor, Json]}

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
        'colors': Annotated[TTextColor, Json]
    }

    @wraps(fn)
    def wrapper(key: str, colors: Annotated[TTextColor, Json]):
        foreground = color_to_tuple(colors['foreground'])
        background = color_to_tuple(colors['background'])
        return fn(key, (foreground, background))

    return wrapper

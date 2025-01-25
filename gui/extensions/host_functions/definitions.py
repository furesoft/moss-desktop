from functools import wraps
from typing import TYPE_CHECKING, Annotated, Optional, Tuple, Union, List

from extism import host_fn as extism_host_fn, Json, ValType
from extism.extism import HOST_FN_REGISTRY

from ..export_types import TColor, TTextColor

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
    fn.__annotations__ = {'key': str, 'r': int, 'g': int, 'b': int, 'a': int}

    @wraps(fn)
    def wrapper(key: str, r: int, g: int, b: int, a: int):
        return fn(key, (r, g, b) if a == 255 else (r, g, b, a))

    return wrapper


def get_color(fn):
    fn.__annotations__ = {'key': str, 'return': Annotated[TColor, Json]}

    @wraps(fn)
    def wrapper(key: str):
        color = fn(key)
        return {
            'r': color[0],
            'g': color[1],
            'b': color[2],
            'a': color[3] if len(color) == 4 else 255
        }

    return wrapper


def get_text_color(fn):
    fn.__annotations__ = {'key': str, 'return': Annotated[TTextColor, Json]}

    @wraps(fn)
    def wrapper(key: str):
        colors = fn(key)
        return {
            'r1': colors[0][0],
            'g1': colors[0][1],
            'b1': colors[0][2],
            'a1': colors[0][3] if len(colors[0]) == 4 else 255,
            **(
                {
                    'r2': colors[1][0],
                    'g2': colors[1][1],
                    'b2': colors[1][2],
                    'a2': colors[1][3] if len(colors[1]) == 4 else 255
                } if colors[1] is not None else {
                    'r2': 0,
                    'g2': 0,
                    'b2': 0,
                    'a2': 0
                }
            )
        }

    return wrapper


def set_text_color(fn):
    fn.__annotations__ = {
        'key': str,
        'r1': int, 'g1': int, 'b1': int, 'a1': int,
        'r2': int, 'g2': int, 'b2': int, 'a2': int
    }

    @wraps(fn)
    def wrapper(key: str, r1: int, g1: int, b1: int, a1: int, r2: int, g2: int, b2: int, a2: int):
        color1 = (r1, g1, b1) if a1 == 255 else (r1, g1, b1, a1)
        color2 = (r2, g2, b2) if a2 == 255 else 0 if a2 == 0 else (r2, g2, b2)
        return fn(key, (color1, color2))

    return wrapper

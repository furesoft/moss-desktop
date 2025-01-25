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
    fn.__annotations__ = {'key': str, 'color': Annotated[TColor, Json]}

    @wraps(fn)
    def wrapper(key: str, color: Annotated[TColor, Json]):
        return fn(
            key,
            (color['r'], color['g'], color['b'])
            if color['a'] is None else
            (color['r'], color['g'], color['b'], color['a'])
        )

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
            'foreground': {
                'r': colors[0][0],
                'g': colors[0][1],
                'b': colors[0][2],
                'a': colors[0][3] if len(colors[0]) == 4 else None,
            },
            'background': (
                {
                    'r': colors[1][0],
                    'g': colors[1][1],
                    'b': colors[1][2],
                    'a': colors[1][3] if len(colors[1]) == 4 else None
                } if colors[1] is not None else None
            )
        }

    return wrapper


def set_text_color(fn):
    fn.__annotations__ = {
        'key': str,
        'colors': Annotated[TTextColor, Json]
    }

    @wraps(fn)
    def wrapper(key: str, colors: Annotated[TTextColor, Json]):
        color1 = (
            (colors['foreground']['r'], colors['foreground']['g'], colors['foreground']['b'])
            if colors['foreground']['a'] is not None and colors['foreground']['a'] == 255 else
            (colors['foreground']['r'], colors['foreground']['g'], colors['foreground']['b'], colors['foreground']['a'])
        )
        color2 = (
            (colors['background']['r'], colors['background']['g'], colors['background']['b'])
            if colors['background']['a'] is not None and colors['background']['a'] > 0 else None) \
            if colors['background'] is not None else None
        return fn(key, (color1, color2))

    return wrapper

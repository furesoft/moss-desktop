from functools import wraps
from typing import TYPE_CHECKING, Annotated, Optional, Tuple, Union, List

from extism import host_fn as extism_host_fn, Json, ValType
from extism.extism import HOST_FN_REGISTRY

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

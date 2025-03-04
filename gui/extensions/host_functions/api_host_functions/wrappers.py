from functools import wraps
from typing import TypedDict, Type, get_origin, Annotated

from box import Box
from extism import Json

from .accessor_handlers import document_inferred
from .export_types import AccessorInstance


def check_ref(func):
    """
    Check if the function accepts a reference to the document or collection.
    """
    has_ref = 'ref' in func.__annotations__
    if has_ref:
        func.__annotations__.pop('ref')
    return has_ref


def blank_ref_wrapper(item_type):
    def wrapper(func):
        @wraps(func)
        def wrapped(item: item_type, *args, **kwargs):
            return func(item, *args, **kwargs)

        return wrapped

    return wrapper


def check_is_dict(_t: Type[TypedDict]):
    return isinstance(_t, type) and issubclass(_t, dict) or get_origin(_t) is dict


def document_wrapper(func):
    """
        This wrapper is for documents.
        Takes in accessor.
    """
    func.__annotations__.pop('item')
    needs_accessor = 'accessor' in func.__annotations__
    if needs_accessor:
        func.__annotations__.pop('accessor')
    func.__annotations__ = {'accessor': Annotated[AccessorInstance, Json], **func.__annotations__}

    @wraps(func)
    def wrapper(accessor: Annotated[AccessorInstance, Json], *args, **kwargs):
        document, _ = document_inferred(box := Box(accessor))
        if needs_accessor:
            args = (box, *args)
        return func(document, *args, **kwargs)

    return wrapper

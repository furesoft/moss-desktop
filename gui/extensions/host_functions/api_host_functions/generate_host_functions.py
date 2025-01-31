from functools import wraps
from typing import TypedDict, Type, Annotated, get_origin, Any

from extism import Json

from rm_api import Document, Metadata, Content, DocumentCollection
from . import export_types as et
from .. import definitions as d


def document_wrapper(func):
    func.__annotations__.pop('item')
    func.__annotations__ = {'document_uuid': str, **func.__annotations__}

    @wraps(func)
    def wrapper(document_uuid: str, *args, **kwargs):
        document = d.api.documents[document_uuid]
        return func(document, *args, **kwargs)

    return wrapper


def document_sub_wrapper(sub_attribute: str):
    def wrapper(func):
        func.__annotations__.pop('item')
        func.__annotations__ = {'document_uuid': str, **func.__annotations__}

        @wraps(func)
        def inner_wrapper(document_uuid: str, *args, **kwargs):
            document = d.api.documents[document_uuid]
            return func(getattr(document, sub_attribute), *args, **kwargs)

        return inner_wrapper

    return wrapper


def collection_wrapper(func):
    func.__annotations__.pop('item')
    func.__annotations__ = {'document_collection_uuid': str, **func.__annotations__}

    @wraps(func)
    def wrapper(document_collection_uuid: str, *args, **kwargs):
        document_collection = d.api.document_collections[document_collection_uuid]
        return func(document_collection, *args, **kwargs)

    return wrapper


def collection_sub_wrapper(sub_attribute: str):
    def wrapper(func):
        func.__annotations__.pop('item')
        func.__annotations__ = {'document_collection_uuid': str, **func.__annotations__}

        @wraps(func)
        def inner_wrapper(document_collection_uuid: str, *args, **kwargs):
            document_collection = d.api.collections[document_collection_uuid]
            return func(getattr(document_collection, sub_attribute), *args, **kwargs)

        return inner_wrapper

    return wrapper


def metadata_wrapper(func):
    func.__annotations__.pop('item')
    func.__annotations__ = {'metadata_id': str, **func.__annotations__}

    @wraps(func)
    def wrapper(metadata_id: str, *args, **kwargs):
        metadata = d.extension_manager.metadata_objects[metadata_id]
        return func(metadata, *args, **kwargs)

    return wrapper


def content_wrapper(func):
    func.__annotations__.pop('item')
    func.__annotations__ = {'content_id': str, **func.__annotations__}

    @wraps(func)
    def wrapper(content_id: str, *args, **kwargs):
        content = d.extension_manager.metadata_objects[content_id]
        return func(content, *args, **kwargs)

    return wrapper


def check_is_dict(_t: Type[TypedDict]):
    return isinstance(_t, type) and issubclass(_t, dict) or get_origin(_t) is dict


def generate_for_type(t: Type[TypedDict], item_type: type, prefix: str, wrapper):
    can_get = {}
    can_set = {}
    for name, _t in t.__annotations__.items():
        is_dict = check_is_dict(_t)

        if is_dict:
            _t = Annotated[_t, Json]

        can_get[name] = _t

        if is_dict:
            continue

        if (prop := getattr(item_type, name, None)) and isinstance(prop, property) and prop.fset is None:
            continue

        if get_origin(_t) is list:
            continue

        can_set[name] = _t

    @d.host_fn(f"{prefix}get")
    @d.transform_to_json
    @wrapper
    def _func(item: item_type, key: str):
        value_type = can_get.get(item, None)
        if not value_type:
            raise ValueError(f"Can't get {key} from {item_type.__name__}")

        if check_is_dict(value_type):
            return getattr(item, key).__dict__
        return getattr(item, key)

    @d.host_fn(f"{prefix}set")
    @wrapper
    def _func(item: item_type, key: str, value: Annotated[Any, Json]):
        value_type = can_set.get(item, None)
        if not value_type:
            raise ValueError(f"Can't set {key} on {item_type.__name__}")
        if type(value) is value_type:
            raise ValueError(
                f"Can't set {key} on {item_type.__name__} "
                f"because type {type(value)} "
                f"does not match required type {value_type}"
            )
        return setattr(item, key, value)

    @d.host_fn(f"{prefix}get_all")
    @wrapper
    def _func(item: t) -> Annotated[t, Json]:
        return item.__dict__


# Top most objects
generate_for_type(et.TRM_Document, Document, "moss_api_document_", document_wrapper)
generate_for_type(et.TRM_DocumentCollection, DocumentCollection, "moss_api_collection_", collection_wrapper)

# Metadata
generate_for_type(et.TRM_MetadataBase, Metadata, "moss_api_collection_metadata_", collection_sub_wrapper('metadata'))
generate_for_type(et.TRM_MetadataDocument, Metadata, "moss_api_document_metadata_", document_sub_wrapper('metadata'))
generate_for_type(et.TRM_MetadataDocument, Metadata, "moss_api_metadata_", metadata_wrapper)

# Content
generate_for_type(et.TRM_Content, Content, "moss_api_document_content_", document_sub_wrapper('content'))
generate_for_type(et.TRM_Content, Content, "moss_api_content_", content_wrapper)

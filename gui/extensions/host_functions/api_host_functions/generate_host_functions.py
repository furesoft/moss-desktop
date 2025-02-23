from functools import wraps
from typing import TypedDict, Type, Annotated, get_origin, Any

from extism import Json

from rm_api import Document, Metadata, Content, DocumentCollection
from . import export_types as et
from .. import definitions as d


def check_ref(func):
    """
    Check if the function accepts a reference to the document or collection.
    """
    has_ref = 'ref' in func.__annotations__
    if has_ref:
        func.__annotations__.pop('ref')
    return has_ref


def document_wrapper(func):
    """
    This wrapper is for documents. Takes in document_uuid.

    api.documents[document_uuid] will be returned.
    """
    func.__annotations__.pop('item')
    ref = check_ref(func)
    func.__annotations__ = {'document_uuid': str, **func.__annotations__}

    @wraps(func)
    def wrapper(document_uuid: str, *args, **kwargs):
        document = d.api.documents[document_uuid]
        if ref:
            kwargs['ref'] = document
        return func(document, *args, **kwargs)

    return wrapper


def document_sub_wrapper(sub_attribute: str):
    """
    This wrapper is for sub attributes of a document. Takes in document_uuid.

    api.documents[document_uuid].sub_attribute will be returned.
    :param sub_attribute: The sub attribute of the document that will be affected
    """

    def wrapper(func):
        func.__annotations__.pop('item')
        ref = check_ref(func)  # The function might accept the reference to the document
        func.__annotations__ = {'document_uuid': str, **func.__annotations__}

        @wraps(func)
        def inner_wrapper(document_uuid: str, *args, **kwargs):
            document = d.api.documents[document_uuid]
            if ref:
                kwargs['ref'] = document  # Pass the document to the function per request
            return func(getattr(document, sub_attribute), *args, **kwargs)

        return inner_wrapper

    return wrapper


def collection_wrapper(func):
    """
    This wrapper is for collections. Takes in collection_uuid.

    api.collections[collection_uuid] will be returned.
    """
    func.__annotations__.pop('item')
    ref = check_ref(func)  # The function might accept the reference to the collection
    func.__annotations__ = {'collection_uuid': str, **func.__annotations__}

    @wraps(func)
    def wrapper(collection_uuid: str, *args, **kwargs):
        document_collection = d.api.document_collections[collection_uuid]
        if ref:
            kwargs['ref'] = document_collection
        return func(document_collection, *args, **kwargs)

    return wrapper


def collection_sub_wrapper(sub_attribute: str):
    """
    This wrapper is for sub attributes of a collection. Takes in collection_uuid.

    api.collections[collection_uuid].sub_attribute will be returned.
    :param sub_attribute: The sub attribute of the document collection that will be affected
    """

    def wrapper(func):
        func.__annotations__.pop('item')
        ref = check_ref(func)  # The function might accept the reference to the collection
        func.__annotations__ = {'collection_uuid': str, **func.__annotations__}

        @wraps(func)
        def inner_wrapper(collection_uuid: str, *args, **kwargs):
            document_collection = d.api.document_collections[collection_uuid]
            if ref:
                kwargs['ref'] = document_collection  # Pass the document collection to the function per request
            return func(getattr(document_collection, sub_attribute), *args, **kwargs)

        return inner_wrapper

    return wrapper


def metadata_wrapper(func):
    """
    This wrapper is for standalone metadata data stored on the extension manager. Takes in metadata_id.

    em.metadata_objects[metadata_id] will be returned.
    """
    func.__annotations__.pop('item')
    func.__annotations__ = {'metadata_id': int, **func.__annotations__}

    @wraps(func)
    def wrapper(metadata_id: int, *args, **kwargs):
        metadata = d.extension_manager.metadata_objects[metadata_id]
        return func(metadata, *args, **kwargs)

    return wrapper


def content_wrapper(func):
    """
    This wrapper is for standalone content data stored on the extension manager. Takes in content_id.
    em.content_objects[content_id] will be returned
    """
    func.__annotations__.pop('item')
    func.__annotations__ = {'content_id': int, **func.__annotations__}

    @wraps(func)
    def wrapper(content_id: int, *args, **kwargs):
        content = d.extension_manager.content_objects[content_id]
        return func(content, *args, **kwargs)

    return wrapper


def ref_wrapper(ref_uuid_key: str, use_item: bool = True):
    # Create a basic wrapper which will add uuid_key to the metadata and content
    def wrapper_generator(item_type):
        def wrapper(func):
            func.__annotations__['ref'] = True

            @wraps(func)
            def wrapped(item: Any, *args, ref, **kwargs):
                # Accepts the item through ref, cause item might be the metadata or content
                item_dict = func(item, *args, **kwargs)
                if (is_document := item_type == Document) or item_type == DocumentCollection:
                    item_dict['metadata'][ref_uuid_key] = ref.uuid
                if is_document:
                    item_dict['content'][ref_uuid_key] = ref.uuid
                if item_type == Metadata or item_type == Content:
                    item_dict[ref_uuid_key] = ref.uuid
                return item_dict

            return wrapped

        return wrapper

    if use_item:  # By default, pass the item as the ref, cause the item would be the document
        def item_wrapper_generator(item_type):
            def item_wrapper(func):
                wrapper = wrapper_generator(item_type)
                wrapped = wrapper(func)
                wrapped.__annotations__.pop('ref')

                @wraps(wrapped)
                def item_wrapped(item: Document, *args, **kwargs):
                    return wrapped(item, *args, ref=item, **kwargs)

                return item_wrapped

            return item_wrapper

        return item_wrapper_generator
    # If the item is not the document or collection, then the ref should be passed from other wrappers

    return wrapper_generator


def blank_ref_wrapper(item_type):
    def wrapper(func):
        @wraps(func)
        def wrapped(item: item_type, *args, **kwargs):
            return func(item, *args, **kwargs)

        return wrapped

    return wrapper


def check_is_dict(_t: Type[TypedDict]):
    return isinstance(_t, type) and issubclass(_t, dict) or get_origin(_t) is dict


def generate_for_type(t: Type[TypedDict], item_type: type, prefix: str, wrapper,
                      extra_item_data_wrapper=blank_ref_wrapper):
    """
    Helper function to generate host functions for a TypedDict type.

    :param t: The TypedDict type
    :param item_type: The type of the item that the TypedDict represents, e.g. Document, Metadata, Content
    :param prefix: The prefix for the host functions
    :param wrapper: A base wrapper to update how the item will be passed to the host functions
    :param extra_item_data_wrapper: A wrapper to update the return value of the host functions to add extra data
    """
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
    @d.debug_result
    @d.transform_to_json
    @wrapper
    def _func(item: item_type, key: str):
        value_type = can_get.get(key, None)
        if not value_type:
            raise ValueError(f"Can't get {key} from {item_type.__name__}")

        if check_is_dict(value_type):
            return getattr(item, key).__dict__
        return getattr(item, key)

    @d.host_fn(f"_{prefix}set")
    @d.debug_result
    @d.unpack
    @wrapper
    def _func(item: item_type, key: str, value: Annotated[Any, Json]):
        value_type = can_set.get(key, None)
        if not value_type:
            raise ValueError(f"Can't set {key} on {item_type.__name__}")
        if type(value) is not value_type:
            raise ValueError(
                f"Can't set {key} on {item_type.__name__} "
                f"because type {type(value)} "
                f"does not match required type {value_type}"
            )
        return setattr(item, key, value)

    @d.host_fn(f"{prefix}get_all")
    @d.debug_result
    @wrapper
    @extra_item_data_wrapper(item_type)
    def _func(item: t) -> Annotated[t, Json]:
        return item.__dict__


# Top most objects
generate_for_type(et.TRM_Document, Document, "moss_api_document_",
                  document_wrapper, ref_wrapper('document_uuid'))
generate_for_type(et.TRM_DocumentCollection, DocumentCollection, "moss_api_collection_",
                  collection_wrapper, ref_wrapper('collection_uuid'))

# Metadata
generate_for_type(et.TRM_MetadataDocument, Metadata,  # Metadata of a document
                  "moss_api_document_metadata_", document_sub_wrapper('metadata'),
                  ref_wrapper('document_uuid', False))
generate_for_type(et.TRM_MetadataBase, Metadata,  # Metadata of a collection
                  "moss_api_collection_metadata_", collection_sub_wrapper('metadata'),
                  ref_wrapper('collection_uuid', False))
generate_for_type(et.TRM_MetadataDocument, Metadata,  # Standalone metadata
                  "moss_api_metadata_", metadata_wrapper)

# Content
generate_for_type(et.TRM_Content, Content, "moss_api_document_content_", document_sub_wrapper('content'),
                  ref_wrapper('document_uuid', False))
generate_for_type(et.TRM_Content, Content, "moss_api_content_", content_wrapper)

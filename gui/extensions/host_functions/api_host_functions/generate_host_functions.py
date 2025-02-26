from pprint import pformat
from typing import TypedDict, Type, Annotated, get_origin, Any

import pygameextra as pe
from colorama import Style, Fore
from extism import Json

from rm_api import Document, Metadata, Content, DocumentCollection
from . import export_types as et
from .export_types import TRM_Tag, TRM_Zoom
from .wrappers import document_wrapper, blank_ref_wrapper, ref_wrapper, collection_wrapper, document_sub_wrapper, \
    collection_sub_wrapper, metadata_wrapper, content_wrapper, check_is_dict
from .. import definitions as d


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
    cannot_get = {}
    can_set = {}
    cannot_set = {}
    for name, _t in t.__annotations__.items():
        is_dict = check_is_dict(_t)

        if is_dict:
            _original = _t
            _t = Annotated[_original, Json]

        can_get[name] = _t

        if (
                (is_dict and _original not in (TRM_Zoom,)) or
                (prop := getattr(item_type, name, None)) and isinstance(prop, property) and prop.fset is None or
                (get_origin(_t) is list and not _t.__args__[0] in (int, str, float, TRM_Tag))
        ):
            cannot_set[name] = _t
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

    if pe.settings.config.debug_log:
        print(f"Generated host functions for `{Style.BRIGHT}{t.__name__}{Style.NORMAL}` "
              f"please not the following restrictions:\n"
              f"CANNOT SET: {Fore.LIGHTGREEN_EX}{pformat(cannot_set)}{Fore.RESET}\n"
              f"CANNOT GET: {Fore.LIGHTYELLOW_EX}{pformat(cannot_get)}{Fore.RESET}")


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

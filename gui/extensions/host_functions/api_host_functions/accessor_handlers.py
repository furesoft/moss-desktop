from functools import partial
from typing import Tuple, Union, Optional

from rm_api import DocumentCollection, Document, Metadata
from .export_types import AccessorInstanceBox, AccessorTypes
from .. import definitions as d


def uuid_accessor_adder(accessor_type: str, dictionary: dict):
    """
        This function adds the accessor to the API/Standalone document and collection objects.
        :param accessor_type: The accessor string
        :param dictionary: The dictionary to add the accessor to
    """
    dictionary['accessor'] = {
        'type': accessor_type,
        'uuid': dictionary['uuid']
    }
    if metadata := dictionary.get('metadata'):
        metadata['accessor'] = {
            'type': f'{accessor_type}_metadata',
            'uuid': dictionary['uuid']
        }
    if content := dictionary.get('content'):
        content['accessor'] = {
            'type': f'{accessor_type}_content',
            'uuid': dictionary['uuid']
        }


def parent_accessor_adder(accessor_type: str, parent: Optional[Union[Document, DocumentCollection]], dictionary: dict,
                          object_id: int = None):
    """
        This function adds the accessor to the metadata and content objects.
        :param accessor_type: The accessor string
        :param parent: An optional parent document or collection object, if the object is not standalone
        :param dictionary: The dictionary to add the accessor to
        :param object_id: An optional object id, if the object is standalone
    """
    dictionary['accessor'] = {
        'type': accessor_type,
    }
    if parent:
        dictionary['accessor']['uuid'] = parent.uuid
    else:
        dictionary['accessor']['id'] = object_id


def document_inferred(accessor: AccessorInstanceBox) -> Tuple[Document, partial]:
    """
        Infer the document object from the accessor instance.
        :param accessor: A box of the accessor instance
        :return: The document object and a function to add the accessor to the dictionary
    """
    getters = {
        AccessorTypes.APIDocument: lambda _: (d.api.documents[_.uuid], partial(uuid_accessor_adder, _.type)),
        AccessorTypes.StandaloneDocument: lambda _: (
            d.extension_manager.document_objects[_.uuid], partial(uuid_accessor_adder, _.type)),
    }

    if (getter := getters.get(AccessorTypes(accessor.type))) is not None:
        return getter(accessor)
    else:
        raise NotImplementedError("This accessor type is not supported for document inferring")


def collection_inferred(accessor: AccessorInstanceBox) -> Tuple[DocumentCollection, partial]:
    """
        Infer the collection object from the accessor instance.
        :param accessor: A box of the accessor instance
        :return: The collection object and a function to add the accessor to the dictionary
    """
    getters = {
        AccessorTypes.APICollection: lambda _: (
            d.api.document_collections[_.uuid], partial(uuid_accessor_adder, _.type)),

        AccessorTypes.StandaloneCollection: lambda _: (
            d.extension_manager.collection_objects[_.uuid], partial(uuid_accessor_adder, _.type)),
    }

    if (getter := getters.get(AccessorTypes(accessor.type))) is not None:
        return getter(accessor)
    else:
        raise NotImplementedError("This accessor type is not supported for collection inferring")


def metadata_inferred(accessor: AccessorInstanceBox) -> Tuple[Metadata, partial]:
    """
        Infer the metadata object from the accessor instance.
        :param accessor: A box of the accessor instance
        :return: The metadata object and a function to add the accessor to the dictionary
    """
    getters = {
        AccessorTypes.APIDocumentMetadata: lambda _: (
            (parent := d.api.documents[_.uuid]).metadata, partial(parent_accessor_adder, _.type, parent)),
        AccessorTypes.APICollectionMetadata: lambda _: (
            (parent := d.api.document_collections[_.uuid]).metadata, partial(parent_accessor_adder, _.type, parent)),

        AccessorTypes.StandaloneDocumentMetadata: lambda _: (
            (parent := d.extension_manager.document_objects[_.uuid]).metadata,
            partial(parent_accessor_adder, _.type, parent)),
        AccessorTypes.StandaloneCollectionMetadata: lambda _: (
            (parent := d.extension_manager.collection_objects[_.uuid]).metadata,
            partial(parent_accessor_adder, _.type, parent)),

        AccessorTypes.StandaloneMetadata: lambda _: (
            obj := d.extension_manager.metadata_objects[_.id],
            partial(parent_accessor_adder, _.type, None, object_id=id(obj))),
    }

    if (getter := getters.get(AccessorTypes(accessor.type))) is not None:
        return getter(accessor)
    else:
        raise NotImplementedError("This accessor type is not supported for metadata inferring")


def content_inferred(accessor: AccessorInstanceBox):
    """
        Infer the content object from the accessor instance.
        :param accessor: A box of the accessor instance
        :return: The content object and a function to add the accessor to the dictionary
    """
    getters = {
        AccessorTypes.APIDocumentContent: lambda _: (
            (parent := d.api.documents[_.uuid]).content, partial(parent_accessor_adder, _.type, parent)),
        AccessorTypes.StandaloneDocumentContent: lambda _: (
            (parent := d.extension_manager.document_objects[_.uuid]).content,
            partial(parent_accessor_adder, _.type, parent)),

        AccessorTypes.StandaloneContent: lambda _: (
            obj := d.extension_manager.content_objects[_.id],
            partial(parent_accessor_adder, _.type, None, object_id=id(obj))),
    }

    if (getter := getters.get(AccessorTypes(accessor.type))) is not None:
        return getter(accessor)
    else:
        raise NotImplementedError("This accessor type is not supported for content inferring")

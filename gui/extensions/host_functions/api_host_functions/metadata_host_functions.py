from typing import Annotated

from box import Box
from extism import Json

from .import_types import MetadataNew
from .. import definitions as d


@d.host_fn()
def moss_api_metadata_new(value: Annotated[MetadataNew, Json]) -> int:
    _ = Box(value)
    metadata = d.api.metadata.new(
        _.name, _.parent, _.document_type
    )
    d.extension_manager.metadata_objects[id(metadata)] = metadata
    return id(metadata)

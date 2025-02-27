from typing import Optional, List, TypedDict, Annotated

from rm_api.defaults import DocumentTypes


class DocumentNewNotebook(TypedDict):
    name: str
    parent: Optional[str]
    document_uuid: Optional[str]
    page_count: int
    notebook_file: Optional[List[str]]
    notebook_data: Optional[List[bytes]]
    metadata_id: Optional[str]
    content_id: Optional[str]


class DocumentNewPDF(TypedDict):
    name: str
    pdf_file: Optional[str]
    pdf_data: Optional[bytes]
    parent: Optional[str]
    document_uuid: Optional[str]


class DocumentNewEPUB(TypedDict):
    name: str
    epub_file: Optional[str]
    epub_data: Optional[bytes]
    parent: Optional[str]
    document_uuid: Optional[str]


class MetadataNew(TypedDict):
    name: str
    parent: Optional[str]
    document_type: Optional[Annotated[DocumentTypes, str]]

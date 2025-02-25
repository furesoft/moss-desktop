from typing import Optional, List, TypedDict


class DocumentNewNotebook(TypedDict):
    name: str
    parent: Optional[str]
    document_uuid: Optional[str]
    page_count: int
    notebook_data: List[str]
    metadata_id: Optional[str]
    content_id: Optional[str]


class DocumentNewPDF(TypedDict):
    name: str
    pdf_data: str
    parent: Optional[str]
    document_uuid: Optional[str]


class DocumentNewEPUB(TypedDict):
    name: str
    epub_data: str
    parent: Optional[str]
    document_uuid: Optional[str]

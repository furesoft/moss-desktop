from io import BytesIO

from PyPDF2 import PdfReader

from rm_api.storage.common import FileHandle


def get_pdf_page_count(pdf: bytes):
    if isinstance(pdf, FileHandle):
        reader = PdfReader(pdf)
    else:
        reader = PdfReader(BytesIO(pdf))

    return len(reader.pages)


from io import BytesIO

from PyPDF2 import PdfReader


def get_pdf_page_count(pdf: bytes):
    reader = PdfReader(BytesIO(pdf))

    return len(reader.pages)

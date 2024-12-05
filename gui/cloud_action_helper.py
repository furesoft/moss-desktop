import io
import pygameextra as pe
import os
from PIL import Image
from PyPDF2 import PdfWriter

from rm_api import Document
from typing import TYPE_CHECKING, List

from rm_api.storage.common import FileHandle

if TYPE_CHECKING:
    from gui import GUI


def import_pdf_to_cloud(gui: 'GUI', file_path):
    pdf_data = FileHandle(file_path)

    parent = gui.main_menu.navigation_parent
    name = os.path.basename(file_path).rsplit('.', 1)[0]  # remove .pdf from the end

    document = Document.new_pdf(gui.api, name, pdf_data, parent)

    document.check()

    gui.import_screen.add_item(document)


def import_files_to_cloud(gui: 'GUI', files):
    files = tuple(
        file for file in files if file.endswith('.pdf')
    )

    gui.import_screen.predefine_item(len(files))

    for file in files:
        if file.endswith('.pdf'):
            import_pdf_to_cloud(gui, file)

def import_notebook_pages_to_cloud(gui: 'GUI', files: List[str], title: str):
    parent = gui.main_menu.navigation_parent


def surfaces_to_pdf(surfaces: List[pe.Surface]):
    pdf_bytes = io.BytesIO()
    images = []

    for surface in (surface.surface for surface in surfaces):
        surface: pe.pygame.Surface
        # Convert the pygame surface to a raw image
        raw_image = pe.pygame.image.tobytes(surface, "RGB")
        width, height = surface.get_size()

        # Create a PIL Image for PDF inclusion
        image = Image.frombytes("RGB", (width, height), raw_image)

        images.append(image)

    images[0].save(
        pdf_bytes,
        "PDF",
        save_all=True,
        resolution=100.0,
        append_images=images[1:]
    )

    return pdf_bytes.getvalue()

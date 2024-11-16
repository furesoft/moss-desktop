import json
import os

from rm_api import Document, Content, Metadata, File, make_uuid, make_hash
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from gui import GUI


def import_pdf_to_cloud(gui: 'GUI', file_path):
    with open(file_path, 'rb') as file:
        pdf_data = file.read()

    parent = gui.main_menu.navigation_parent
    name = os.path.basename(file_path).rsplit('.', 1)[0]  # remove .pdf from the end

    document = Document.new_pdf(gui.api, name, pdf_data, parent)

    gui.import_screen.add_item(document)

import json
import os

from rm_api import Document, Content, Metadata, File, make_uuid, make_hash
from typing import TYPE_CHECKING, Union

from rm_api.storage.common import FileHandle

if TYPE_CHECKING:
    from gui import GUI


def import_pdf_to_cloud(gui: 'GUI', file_path):
    pdf_data = FileHandle(file_path)

    parent = gui.main_menu.navigation_parent
    name = os.path.basename(file_path).rsplit('.', 1)[0]  # remove .pdf from the end

    document = Document.new_pdf(gui.api, name, pdf_data, parent)

    gui.import_screen.add_item(document)



def import_files_to_cloud(gui: 'GUI', files):
    files = tuple(
        file for file in files if file.endswith('.pdf')
    )

    gui.import_screen.predefine_item(len(files))

    for file in files:
        if file.endswith('.pdf'):
            import_pdf_to_cloud(gui, file)

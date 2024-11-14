import json
import os

from rm_api import Document, Content, Metadata, File, make_uuid, make_hash
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from gui import GUI
    from gui.screens.main_menu import MainMenu


def import_pdf_to_cloud(gui: Union['GUI', 'MainMenu'], file_path):
    with open(file_path, 'rb') as file:
        pdf_data = file.read()

    if type(gui).__name__ == 'MainMenu':
        parent = gui.navigation_parent
    else:
        parent = None

    document_uuid = make_uuid()

    content = Content.new_pdf()
    metadata = Metadata.new(os.path.basename(file_path), parent)
    pagedata = b'Blank\n'

    content_uuid = f'{document_uuid}.content'
    metadata_uuid = f'{document_uuid}.metadata'
    pagedata_uuid = f'{document_uuid}.pagedata'
    pdf_uuid = f'{document_uuid}.pdf'

    content_data = {
        content_uuid: json.dumps(content.to_dict(), indent=4),
        metadata_uuid: json.dumps(metadata.to_dict(), indent=4),
        pagedata_uuid: pagedata,
        pdf_uuid: pdf_data
    }

    content_hashes = {
        content_uuid: content.hash,
        metadata_uuid: metadata.hash,
        pagedata_uuid: make_hash(pagedata),
        pdf_uuid: make_hash(pdf_data)
    }

    document = Document(gui.api, content, metadata, [
        File(content_hashes[key], key, 0, len(content))
        for key, content in content_data.items()
    ], document_uuid)

    document.content_data = content_data
    document.files_available = {file.uuid: file for file in document.files}

    gui.api.upload(document)

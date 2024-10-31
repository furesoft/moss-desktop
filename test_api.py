from io import BytesIO

from slashr import SlashR
from rm_api import API, get_file
from rm_api.models import now_time
from rm_lines import tree_to_svg, rm_bytes_to_svg
from rm_lines.blocks import read_blocks

api = API()

with SlashR(False) as sr:
    items = 1
    last_update_time = 0
    done = 0


    def track_progress(i, d):
        global items, done
        items = d
        done = i


    api.get_documents(track_progress)

    while done < items:
        sr.print(f"Downloading documents... {done}/{items}")
    sr.print(f"Downloaded {items} documents")

meows = set()
for document in api.documents.values():
    if 'meow' in document.metadata.visible_name:
        document.metadata.last_opened = now_time()
        document.metadata.created_time = now_time()
        document.metadata.last_modified = now_time()
        document.parent = None
        api.upload(document)
    meows.add(document.metadata.visible_name)

for i in range(3):
    name = f"meow {i}"
    if name in meows:
        continue
    document = api.new_notebook(name)
    document.parent = 'trash'
    api.upload(document)


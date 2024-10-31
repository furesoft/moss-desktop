import json
import threading
import time
from io import BytesIO

from slashr import SlashR
from rm_api import API, get_file, update_root, put_file, make_files_request
from rm_api.models import now_time, File, make_hash
from rm_lines import tree_to_svg, rm_bytes_to_svg
from rm_lines.blocks import read_blocks

with open('config.json', 'r') as f:
    config = json.load(f)

api = API(uri=config['uri'], discovery_uri=config['discovery_uri'])

data = b'3\n'

print(make_hash(data))

# api.check_for_document_storage()
# file = File(make_hash(data), 'root.docSchema', 0, len(data))
# # put_file(api, file, data)
# update_root(api, {
#     'hash': file.hash,
#     'generation': 0,
# })
#
# exit()

with SlashR(False) as sr:
    items = 0
    last_update_time = 0
    done = 0


    def track_progress(i, d):
        global items, done
        items = d
        done = i

    threading.Thread(target=api.get_documents, args=(track_progress,), daemon=True).start()

    time.sleep(.2)
    while done < items:
        sr.print(f"Downloading documents... {done}/{items}")
    sr.print(f"Downloaded {items} documents")

meows = set()
for document in api.documents.values():
    meows.add(document.metadata.visible_name)
# print('\n'*10)
# print(make_files_request(api, 'GET', api.get_root()['hash'], use_cache=False))

for i in range(2):
    name = f"meow {i}"
    if name in meows:
        continue
    document = api.new_notebook(name)
    api.upload(document)


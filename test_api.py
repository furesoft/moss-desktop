import json
import threading
import time
from io import BytesIO

from slashr import SlashR
from rm_api import API, get_file, update_root, put_file, make_files_request, Document, FileSyncProgress
from rm_api.models import now_time, File, make_hash
from rm_lines import tree_to_svg, rm_bytes_to_svg
from rm_lines.blocks import read_blocks

with open('config.json', 'r') as f:
    config = json.load(f)

api = API(uri=config['uri'], discovery_uri=config['discovery_uri'])
api.debug = True

with SlashR(False) as sr:
    items = 0
    last_update_time = 0
    done = 0


    def track_progress(items_done, items_total):
        global items, done, last_update_time
        items = items_total
        done = items_done
        last_update_time = time.time()


    threading.Thread(target=api.get_documents, args=(track_progress,), daemon=True).start()

    while last_update_time <= 0:
        pass
    while done < items:
        sr.print(f"Downloading documents... {done}/{items}")
    sr.print(f"Downloaded {items} documents")

meows = set()
for document in api.documents.values():
    meows.add(document.metadata.visible_name)

with open('large.pdf', 'rb') as f:
    large = f.read()

docs = []
for i in range(50):
    name = f"this is a very accurate test ;3 [{i}]"
    print(name)
    if name in meows:
        continue
    docs.append(Document.new_pdf(api, name, large, '161d5d4a-c5a1-428c-91d8-d29401348fb5'))

done = False
ev: FileSyncProgress = None


def subscribed(e):
    global ev
    if isinstance(e, FileSyncProgress):
        ev = e


api.add_hook('sub', subscribed)
threading.Thread(target=api.upload_many_documents, args=(docs,), daemon=True).start()

while not ev:
    pass
with SlashR(False) as sr:
    while not ev.finished:
        sr.print(f'{ev.done} / {ev.total}')
        time.sleep(.1)

time.sleep(10)

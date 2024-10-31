from io import BytesIO

from slashr import SlashR
from rm_api import API
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

document = api.new_notebook("testC")

api.upload(document)
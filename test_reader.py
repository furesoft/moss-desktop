import io

from rm_lines import read_tree, tree_to_svg

with open(
        # "sync_exports/560cb128-7cf4-478b-8a0a-3cff10706685/35f61c99-e2d6-463e-a6ee-704d817fa999/6c12e328-8c3b-4eb0-abbe-39697248fbac.rm",
        "sync_exports/928542fd-6225-4623-9306-803c038ee5d4/95369510-8d35-4685-aeba-0aaaddd4c998/8f6b581a-311a-490b-a89b-4dfbc5be0e15.rm",
        "rb") as f:
    data = f.read()


tree = read_tree(io.BytesIO(data))


with open("test.svg", "wt") as f:
    tree_to_svg(tree, f)
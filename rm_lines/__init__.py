from io import BytesIO, StringIO
from .reader import read_tree
from .inker import tree_to_svg


def rm_bytes_to_svg(data: bytes):
    tree = read_tree(BytesIO(data))
    with StringIO() as f:
        tree_to_svg(tree, f)
        return f.getvalue()


__all__ = ['read_tree', 'tree_to_svg']

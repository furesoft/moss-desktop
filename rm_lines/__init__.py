from io import BytesIO, StringIO

from rm_lines.inker.document_size_tracker import DocumentSizeTracker
from .reader import read_tree
from .inker import tree_to_svg


def rm_bytes_to_svg(data: bytes, track_xy: DocumentSizeTracker = None):
    tree = read_tree(BytesIO(data))
    with StringIO() as f:
        tree_to_svg(tree, f, track_xy)
        return f.getvalue()


__all__ = ['read_tree', 'tree_to_svg']

from io import BytesIO, StringIO
from pprint import pprint

from pygameextra import settings

from rm_lines.inker.document_size_tracker import DocumentSizeTracker
from .crdt_sequence import CrdtSequence
from .inker import tree_to_svg
from .reader import read_tree


def get_children(sequence: CrdtSequence):
    return [
        get_children(child) if getattr(child, 'children', None) else child
        for child in map(lambda child_id: sequence.children[child_id], sequence.children)
    ]


def rm_bytes_to_svg(data: bytes, track_xy: DocumentSizeTracker = None):
    tree = read_tree(BytesIO(data))

    if settings.config.debug_lines:
        pprint(get_children(tree.root))

    with StringIO() as f:
        tree_to_svg(tree, f, track_xy)
        return f.getvalue()


__all__ = ['read_tree', 'tree_to_svg']

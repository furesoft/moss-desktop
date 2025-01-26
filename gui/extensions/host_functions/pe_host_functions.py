from typing import Annotated

import pygameextra as pe
from extism import Json

from . import definitions as d
from ..input_types import color_to_tuple, rect_to_pe_rect, TPygameExtraRect


@d.host_fn('_moss_pe_draw_rect')
def moss_pe_draw_rect(draw: Annotated[TPygameExtraRect, Json]):
    color, rect, width, edge_rounding = draw['color'], draw['rect'], draw['width'], draw['edge_rounding'] or {}
    pe.draw.rect(
        color_to_tuple(color), rect_to_pe_rect(rect), width,
        edge_rounding=edge_rounding.get('edge_rounding', -1) or -1,
        edge_rounding_topright=edge_rounding.get('edge_rounding_topright', -1) or -1,
        edge_rounding_topleft=edge_rounding.get('edge_rounding_topleft', -1) or -1,
        edge_rounding_bottomright=edge_rounding.get('edge_rounding_bottomright', -1) or -1,
        edge_rounding_bottomleft=edge_rounding.get('edge_rounding_bottomleft', -1) or -1
    )

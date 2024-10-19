from typing import Dict

import pygameextra as pe
from functools import lru_cache


class PreviewHandler:
    CACHED_PREVIEW: Dict[pe.Image]

from . import definitions as d
from ...defaults import Defaults


# Defaults

@d.host_fn()
def moss_defaults_set_color(key: str, r: int, g: int, b: int, a: int):
    setattr(Defaults, key, (r, g, b, a))


@d.host_fn()
def moss_defaults_set_text_color(key: str, r1: int, g1: int, b1: int, r2: int, g2: int, b2: int):
    setattr(Defaults, key, [(r1, g1, b1), (r2, g2, b2) if r2 > 0 else None])

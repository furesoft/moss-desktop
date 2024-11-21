from typing import Literal

MAIN_MENU_MODES = Literal['grid', 'list', 'compressed']
PDF_RENDER_MODES = Literal['cef', 'pymupdf', 'none', 'retry']
NOTEBOOK_RENDER_MODES = Literal['rm_lines_svg_inker']